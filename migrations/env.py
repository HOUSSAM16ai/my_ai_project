import logging
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import your app's models to register them with SQLModel.metadata
from app import models  # noqa: F401

# Import the robust sanitization logic
# We need to add the scripts directory to path temporarily if we want to reuse it,
# but it's cleaner to just rely on the environment variable which was ALREADY processed by bootstrap_db.py
# in setup_dev.sh. However, for safety inside env.py (e.g. running alembic directly),
# we implement a robust getter.

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

    # FIX: Supabase/PgBouncer Transaction Mode
    # Apply to all non-SQLite databases (targeting Supabase/Postgres/Asyncpg)
    if "sqlite" not in DATABASE_URL:
        # 1. Disable prepared statements for PgBouncer transaction mode
        connect_args["statement_cache_size"] = 0

        # 2. Set a connection timeout to prevent infinite hangs
        # 'command_timeout' is for queries, 'timeout' is for connection
        connect_args["timeout"] = 30  # 30 seconds connection timeout
        connect_args["command_timeout"] = 60

        # 3. SSL is usually handled by the query param ?ssl=require in the URL
        # which we ensured in get_database_url / bootstrap_db.py

    logger.info(f"Connecting to database with args: {connect_args.keys()}")

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
