import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

# Import Unified Engine Factory
from app.core.engine_factory import create_unified_async_engine

# Import your app's models to register them with SQLModel.metadata
try:
    from app import models  # noqa: F401
except ImportError as e:
    print(f"CRITICAL: Could not import app.models: {e}")
    sys.exit(1)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

load_dotenv(override=False)

def get_database_url():
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    # The factory handles scheme correction, but we pass it raw or semi-raw
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


def do_run_migrations_sync(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using the UNIFIED ENGINE FACTORY."""

    logger.info(f"🔄 Migrating using UNIFIED ENGINE FACTORY...")

    # Use the factory to create the engine.
    # EXPLICITLY enforcing statement_cache_size=0 to prevent PgBouncer errors.
    connect_args = {"statement_cache_size": 0} if "sqlite" not in DATABASE_URL else {}

    connectable = create_unified_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        connect_args=connect_args
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations_sync)

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
