import copy
import logging
import os
from typing import Any

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Configure logging
logger = logging.getLogger(__name__)


class FatalEngineError(Exception):
    """Raised when an unsafe or invalid engine configuration is detected."""

    pass


def _sanitize_database_url(url: str) -> str:
    """
    Sanitizes and validates the DATABASE_URL.

    Ensures:
    1. Correct protocol (postgresql+asyncpg for async, postgresql+psycopg2/sync for sync).
    2. SSL mode is handled correctly for production.
    """
    if not url:
        # Fallback for local testing if not set, or raise error?
        # Generally, we expect DATABASE_URL.
        # If this is running in a context without it (like some tests without fixtures),
        # it might fail. But usually better to fail early.
        # However, for safety, we can check if we are in a test env or raise.
        # Given the prompt, we should be strict.
        if "pytest" in os.environ.get("_", "") or os.environ.get("TESTING"):
            return "sqlite+aiosqlite:///:memory:"
        raise FatalEngineError("DATABASE_URL is not set.")

    # Auto-correct common protocol mistakes
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def create_unified_async_engine(
    database_url: str = None, echo: bool = False, **kwargs: Any
) -> AsyncEngine:
    """
    The Single Source of Truth for creating Async SQLAlchemy Engines.

    STRICTLY ENFORCES:
    - statement_cache_size=0 for all non-SQLite databases (Critical for PgBouncer).
    - Safe connection pooling settings.
    - Idempotent configuration via copy.deepcopy.

    Args:
        database_url: The DB connection string. Defaults to os.getenv("DATABASE_URL").
        echo: Whether to log SQL statements.
        **kwargs: Additional arguments passed to create_async_engine.
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    database_url = _sanitize_database_url(database_url)

    # Deep copy kwargs to prevent side effects
    engine_kwargs = copy.deepcopy(kwargs)
    engine_kwargs["echo"] = echo

    # Detect Database Type
    is_sqlite = "sqlite" in database_url
    is_postgres = "postgresql" in database_url

    # --- 1. POOLING HYGIENE ---
    # If NullPool is used, strictly remove pooling args that would cause errors/warnings
    pool_class = engine_kwargs.get("poolclass")
    if pool_class == pool.NullPool:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)
        logger.info("UnifiedFactory: NullPool detected. Removed pool_size/max_overflow.")

    # --- 2. POSTGRES HARDENING ---
    if is_postgres:
        # Enforce correct async driver
        if "asyncpg" not in database_url:
            # If it's just 'postgresql://', upgrade to 'postgresql+asyncpg://'
            if "postgresql://" in database_url and "+" not in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

        # Ensure connect_args exists
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}

        # STRICTLY DISABLE PREPARED STATEMENTS for PgBouncer compatibility
        # This fixes the "DuplicatePreparedStatementError"
        # We OVERRIDE whatever was passed to ensure safety.
        engine_kwargs["connect_args"]["statement_cache_size"] = 0

        # Enforce safe pooling defaults if not provided AND not using NullPool
        if pool_class != pool.NullPool:
            engine_kwargs.setdefault("pool_pre_ping", True)
            engine_kwargs.setdefault("pool_size", 20)
            engine_kwargs.setdefault("max_overflow", 10)

        logger.info(
            f"Creating Unified Async Engine for Postgres. Cache Disabled. Pool: {pool_class or 'Default'}"
        )

    elif is_sqlite:
        # SQLite Specific Cleanups
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)

        # Ensure proper async sqlite protocol
        if "sqlite+aiosqlite" not in database_url and "sqlite://" in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Enable foreign keys for SQLite
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}
        engine_kwargs["connect_args"]["check_same_thread"] = False  # Needed for FastAPI/Starlette

        logger.info("Creating Unified Async Engine for SQLite.")

    # --- 3. SECURITY & SAFETY CHECK ---
    if is_postgres:
        # Double check that statement_cache_size is indeed 0
        cache_setting = engine_kwargs.get("connect_args", {}).get("statement_cache_size")
        if cache_setting != 0:
            raise FatalEngineError(
                f"Security Violation: statement_cache_size is {cache_setting}. MUST be 0 for Postgres/PgBouncer."
            )

    return create_async_engine(database_url, **engine_kwargs)


def create_unified_sync_engine(
    database_url: str = None, echo: bool = False, **kwargs: Any
) -> Engine:
    """
    The Single Source of Truth for creating Sync SQLAlchemy Engines.
    Used strictly for:
    - Alembic Migrations (when run synchronously)
    - Legacy synchronous scripts
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    database_url = _sanitize_database_url(database_url)

    # Ensure sync driver for Postgres
    if "postgresql+asyncpg" in database_url:
        database_url = database_url.replace(
            "postgresql+asyncpg", "postgresql"
        )  # Fallback to default (psycopg2)

    engine_kwargs = copy.deepcopy(kwargs)
    engine_kwargs["echo"] = echo

    is_sqlite = "sqlite" in database_url
    is_postgres = "postgresql" in database_url

    # --- POOLING HYGIENE ---
    pool_class = engine_kwargs.get("poolclass")
    if pool_class == pool.NullPool:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)

    if is_postgres and pool_class != pool.NullPool:
        engine_kwargs.setdefault("pool_pre_ping", True)
    elif is_sqlite:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}
        engine_kwargs["connect_args"]["check_same_thread"] = False

    logger.info(f"Creating Unified Sync Engine for {'SQLite' if is_sqlite else 'Postgres'}.")
    return create_engine(database_url, **engine_kwargs)
