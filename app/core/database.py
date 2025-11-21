import os
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# ARCHITECTURAL FIX: Unified Source of Truth
# We prefer the strictly sanitized DATABASE_URL from the environment (set by bootstrap)
# over the one potentially mutated by Pydantic.
# ------------------------------------------------------------------------------
def get_connection_string() -> str:
    """
    Retrieves the database URL with strict enforcement of asyncpg and SSL.
    Prioritizes os.environ['DATABASE_URL'] if available and valid.
    """
    url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

    if not url:
        # Fallback for CI/Test if not set
        return "sqlite+aiosqlite:///./test.db"

    # Force Scheme: postgresql+asyncpg://
    if "postgresql://" in url and "postgresql+asyncpg://" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif "postgres://" in url:
        url = url.replace("postgres://", "postgresql+asyncpg://")

    # Force SSL Logic (Programmatic)
    # asyncpg expects 'ssl=require' in query params or explicit ssl context.
    # We ensure 'sslmode' legacy param is removed if present to avoid conflicts.
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")

    return url

FINAL_DATABASE_URL = get_connection_string()

# ------------------------------------------------------------------------------
# SUPABASE HARDENING
# ------------------------------------------------------------------------------
# PgBouncer in transaction mode does not support prepared statements.
# We must disable them globally for asyncpg.
# ------------------------------------------------------------------------------
connect_args = {}
# FIX: Apply to all non-SQLite databases (targeting Supabase/Postgres/Asyncpg)
if "sqlite" not in FINAL_DATABASE_URL:
    # 1. Disable prepared statements
    connect_args["statement_cache_size"] = 0
    # 2. Add timeouts to avoid silent hangs
    connect_args["timeout"] = 30
    connect_args["command_timeout"] = 60
else:
    # For SQLite (tests), we might want other args, but no cache fix needed
    pass

# GLOBAL SAFETY NET: Warn if we are about to create an engine that might crash on PgBouncer
if "postgresql" in FINAL_DATABASE_URL and connect_args.get("statement_cache_size") != 0:
    logger.critical(
        "🚨 FATAL CONFIGURATION ERROR: Creating Async Engine for Postgres WITHOUT statement_cache_size=0. "
        "This will crash on Supabase/PgBouncer!"
    )
    # Force the fix if it was somehow missed (Double Safety)
    connect_args["statement_cache_size"] = 0

# Create Async Engine
engine = create_async_engine(
    FINAL_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ------------------------------------------------------------------------------
# SYNC ENGINE RESTRICTION (SUPRA-EXECUTIVE DIRECTIVE)
# ------------------------------------------------------------------------------
# We must eliminate ALL sync engine connections to Supabase to prevent DuplicatePreparedStatementError.
# If DATABASE_URL is Postgres, we disable the sync engine completely.
# ------------------------------------------------------------------------------

SYNC_DATABASE_URL = FINAL_DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
sync_engine = None

if "sqlite" in SYNC_DATABASE_URL:
    # Allow Sync Engine for SQLite (Tests/Local)
    sync_connect_args = {"check_same_thread": False}
    sync_engine = create_engine(
        SYNC_DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        connect_args=sync_connect_args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
else:
    # DISABLE SYNC ENGINE FOR POSTGRES
    # We create a "Trap" class that raises an error if instantiated or used.
    class SyncEngineTrap:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            raise RuntimeError(
                "🚨 CRITICAL ERROR: Sync Database Engine is DISABLED for Supabase/Postgres. "
                "You must use the Async Engine (await db.execute) to avoid PgBouncer errors."
            )
        def __getattr__(self, name):
            raise RuntimeError(
                f"🚨 CRITICAL ERROR: Attempted to access '{name}' on Sync Engine, which is DISABLED for Supabase/Postgres."
            )

    SessionLocal = SyncEngineTrap
    sync_engine = None # Explicitly None to catch direct usage

    logger.info("🔒 Sync Engine DISABLED for Production/Postgres to prevent PgBouncer conflicts.")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
