import asyncio
import logging
import os
from logging.config import fileConfig

from dotenv import load_dotenv

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import your app's models to register them with SQLModel.metadata
from app import models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Load environment variables from .env file if present
load_dotenv()

# ------------------------------------------------------------------------------
# FIX: Bypass ConfigParser interpolation & Pydantic settings
# We read the DATABASE_URL directly from os.environ to avoid issues with
# special characters (like %) in the URL.
# ------------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

def fix_database_url(url: str) -> str:
    """
    Auto-fix the database URL for asyncpg compatibility.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Fix SSL mode
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")

    return url

DATABASE_URL = fix_database_url(DATABASE_URL)

# Your models' metadata for 'autogenerate' support
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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


def run_migrations_online() -> None:
    # BYPASS CONFIG PARSER: Read directly from env or bootstrap
    connectable = create_async_engine(
        os.environ.get("DATABASE_URL"), # Logic: The URL is already sanitized by the bootstrap script
        poolclass=pool.NullPool,
        connect_args={"statement_cache_size": 0} # FIX: Supabase PgBouncer Compatibility
    )

    def do_run_migrations_sync(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations_sync)

    import asyncio
    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
