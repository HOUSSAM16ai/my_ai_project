import logging
import os
import sys
from logging.config import fileConfig
from urllib.parse import urlparse

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

# Import your app's models to register them with SQLModel.metadata
try:
    from app import models  # noqa: F401
except ImportError as e:
    print(f"CRITICAL: Could not import app.models: {e}")
    sys.exit(1)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Load environment variables from .env file if present
load_dotenv(override=False)

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
def get_database_url():
    """
    Get the DATABASE_URL from environment.
    If it's not set, fall back to SQLite.
    We assume the URL in env var is already sanitized by scripts/bootstrap_db.py if run via setup_dev.sh.
    If run manually, we apply minimal fixes.
    """
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

    # Defensive fixes if not running through bootstrap
    if url.startswith("postgres"):
        if "postgresql+asyncpg" not in url:
             if url.startswith("postgres://"):
                 url = url.replace("postgres://", "postgresql+asyncpg://", 1)
             elif url.startswith("postgresql://"):
                 url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        if "sslmode=require" in url:
            url = url.replace("sslmode=require", "ssl=require")

    return url

DATABASE_URL = get_database_url()
target_metadata = SQLModel.metadata


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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""

    # --------------------------------------------------------------------------
    # SUPABASE / PGBOUNCER CONFIGURATION
    # --------------------------------------------------------------------------
    connect_args = {}

    # Explicitly check for asyncpg usage via URL scheme or driver
    if "sqlite" not in DATABASE_URL:
        # Enforce statement_cache_size=0 for ALL Postgres connections
        connect_args = {"statement_cache_size": 0, "timeout": 30, "command_timeout": 60}

        # Double check: Log the exact configuration
        logger.info(f"🔧 FORCE-APPLYING PgBouncer Fix: statement_cache_size=0")
        logger.info(f"🔧 Connection Args: {connect_args}")

    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        connect_args=connect_args,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations_sync)

    await connectable.dispose()


def do_run_migrations_sync(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import asyncio

    # Use current loop or create new one
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
