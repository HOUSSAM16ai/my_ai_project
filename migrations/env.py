import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel

# ------------------------------------------------------------------------------
# 🛡️ MIGRATION SECURITY LAYER
# ------------------------------------------------------------------------------
# Ensure strict isolation and correct path resolution
sys.path.append(os.getcwd())

# Import Unified Engine Factory
# This must be the ONLY way an engine is created.
try:
    from app.core.engine_factory import create_unified_async_engine
except ImportError as e:
    print(f"🔥 CRITICAL ERROR: Could not import Unified Engine Factory: {e}")
    sys.exit(1)

# Import Models for Metadata
try:
    from app import models  # noqa: F401
except ImportError as e:
    print(f"⚠️ WARNING: Could not import app.models: {e}")
    # We continue, as sometimes we might only need raw SQL, but usually this is bad.

# Load Config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Logger
logger = logging.getLogger("alembic.env")

# Load Environment
load_dotenv(override=False)

# ------------------------------------------------------------------------------
# 🔧 CONFIGURATION
# ------------------------------------------------------------------------------

def get_database_url():
    """
    Retrieves the DATABASE_URL from environment.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback for local testing if absolutely needed, but we prefer env var
        logger.warning("⚠️ DATABASE_URL not set in environment. Using default SQLite fallback.")
        return "sqlite+aiosqlite:///./test.db"
    return url

DATABASE_URL = get_database_url()
target_metadata = SQLModel.metadata

# ------------------------------------------------------------------------------
# 🚀 MIGRATION LOGIC
# ------------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations_sync(connection: Connection) -> None:
    """
    Sync helper to run migrations.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using the UNIFIED ENGINE FACTORY.
    """
    logger.info("🔄 INITIALIZING MIGRATION CONTEXT (Unified Mode)")

    # 1. SECURITY CHECK
    if not DATABASE_URL:
        logger.error("❌ CRITICAL: DATABASE_URL is missing.")
        sys.exit(1)

    # 2. CONFIGURE CONNECT ARGS
    # We explicity set statement_cache_size=0 here as a fail-safe,
    # although the factory also enforces it.
    is_sqlite = "sqlite" in DATABASE_URL

    connect_args = {}
    if not is_sqlite:
        connect_args["statement_cache_size"] = 0
        logger.info("🛡️  Enforcing statement_cache_size=0 for Migration Engine")

    # 3. CREATE ENGINE
    # We rely 100% on the factory to handle the engine creation details.
    try:
        connectable = create_unified_async_engine(
            DATABASE_URL,
            poolclass=pool.NullPool, # Migrations don't need a pool
            connect_args=connect_args
        )
    except Exception as e:
        logger.error(f"❌ FAILED to create migration engine: {e}")
        sys.exit(1)

    # 4. EXECUTE MIGRATION
    try:
        async with connectable.connect() as connection:
            # Verify connection args were applied (if possible to inspect)
            logger.info("✅ Connected to database. Running migrations...")
            await connection.run_sync(do_run_migrations_sync)
    except Exception as e:
        logger.error(f"💥 MIGRATION ERROR: {e}")
        if "DuplicatePreparedStatementError" in str(e):
            logger.critical("💣 DETECTED DUPLICATE PREPARED STATEMENT ERROR")
            logger.critical("   Ensure PgBouncer is configured with pool_mode=transaction")
            logger.critical("   and statement_cache_size=0 is active.")
        raise e
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
