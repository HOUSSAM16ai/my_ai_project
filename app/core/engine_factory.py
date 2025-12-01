import copy
import logging
import os
from typing import Any
from uuid import uuid4

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
        if "pytest" in os.environ.get("_", "") or os.environ.get("TESTING"):
            return "sqlite+aiosqlite:///:memory:"
        raise FatalEngineError("DATABASE_URL is not set.")

    # Auto-correct common protocol mistakes
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Auto-fix SSL Mode: libpq 'sslmode' -> asyncpg 'ssl'
    # This prevents TypeError: connect() got an unexpected keyword argument 'sslmode'
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    elif "sslmode=disable" in url:
        url = url.replace("sslmode=disable", "ssl=disable")
    elif "sslmode=allow" in url:
        url = url.replace("sslmode=allow", "ssl=allow")
    elif "sslmode=prefer" in url:
        url = url.replace("sslmode=prefer", "ssl=prefer")
    elif "sslmode=verify-ca" in url:
        url = url.replace("sslmode=verify-ca", "ssl=verify-ca")
    elif "sslmode=verify-full" in url:
        url = url.replace("sslmode=verify-full", "ssl=verify-full")

    return url


def create_unified_async_engine(
    database_url: str | None = None, echo: bool = False, **kwargs: Any
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
        if (
            "asyncpg" not in database_url
            and "postgresql://" in database_url
            and "+" not in database_url
        ):
            # If it's just 'postgresql://', upgrade to 'postgresql+asyncpg://'
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

        # Ensure connect_args exists
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}

        # =============================================================================
        # CRITICAL FIX FOR PgBouncer TRANSACTION POOLING COMPATIBILITY
        # =============================================================================
        # Problem: PgBouncer in transaction pooling mode shares connections between
        # different sessions. Server-side prepared statements created in one session
        # may not exist when the connection is reused by another session, causing:
        # "InvalidSQLStatementNameError: prepared statement '_asyncpg_stmt_X' does not exist"
        #
        # Solution: Disable ALL prepared statement caching at TWO levels:
        #
        # 1. asyncpg level (statement_cache_size=0):
        #    Disables asyncpg's internal prepared statement cache on the raw connection.
        #
        # 2. SQLAlchemy asyncpg dialect level (prepared_statement_cache_size=0):
        #    Disables SQLAlchemy's DBAPI-level prepared statement cache.
        #    This is the cache that causes "_asyncpg_stmt_X" errors with PgBouncer.
        #
        # 3. Unique prepared statement names (prepared_statement_name_func):
        #    As an additional safety measure, we use UUID-based names for any
        #    prepared statements that might still be created, preventing collisions
        #    across different sessions sharing the same connection.
        # =============================================================================

        # Level 1: Disable asyncpg's native prepared statement cache
        engine_kwargs["connect_args"]["statement_cache_size"] = 0

        # Level 2: Disable SQLAlchemy asyncpg dialect's prepared statement cache
        # This is the CRITICAL fix for the "_asyncpg_stmt_X does not exist" error
        engine_kwargs["connect_args"]["prepared_statement_cache_size"] = 0

        # Level 3: Use unique prepared statement names to prevent collisions
        # Even with caching disabled, some operations might create prepared statements.
        # Using UUID-based names ensures no conflicts when connections are reused.
        engine_kwargs["connect_args"]["prepared_statement_name_func"] = (
            lambda: f"__asyncpg_{uuid4()}__"
        )

        # Also enforce command_timeout to avoid hanging queries
        engine_kwargs["connect_args"].setdefault("command_timeout", 60)

        # Enforce safe pooling defaults if not provided AND not using NullPool
        if pool_class != pool.NullPool:
            engine_kwargs.setdefault("pool_pre_ping", True)
            engine_kwargs.setdefault("pool_size", 20)
            engine_kwargs.setdefault("max_overflow", 10)
            # Enable automatic reconnection
            engine_kwargs.setdefault("pool_recycle", 300)

        logger.info(
            f"Creating Unified Async Engine for Postgres with PgBouncer-safe settings. "
            f"Connect Args: statement_cache_size=0, prepared_statement_cache_size=0, "
            f"prepared_statement_name_func=UUID. Pool: {pool_class or 'Default'}"
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
        connect_args = engine_kwargs.get("connect_args", {})

        # Verify statement_cache_size is 0
        cache_setting = connect_args.get("statement_cache_size")
        if cache_setting != 0:
            raise FatalEngineError(
                f"Security Violation: statement_cache_size is {cache_setting}. MUST be 0 for Postgres/PgBouncer."
            )

        # Verify prepared_statement_cache_size is 0
        prepared_cache_setting = connect_args.get("prepared_statement_cache_size")
        if prepared_cache_setting != 0:
            raise FatalEngineError(
                f"Security Violation: prepared_statement_cache_size is {prepared_cache_setting}. "
                "MUST be 0 for Postgres/PgBouncer compatibility."
            )

        # Verify prepared_statement_name_func is set
        if "prepared_statement_name_func" not in connect_args:
            raise FatalEngineError(
                "Security Violation: prepared_statement_name_func is not set. "
                "Required for PgBouncer compatibility."
            )

    return create_async_engine(database_url, **engine_kwargs)


def create_unified_sync_engine(
    database_url: str | None = None, echo: bool = False, **kwargs: Any
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

    # Revert 'ssl=require' back to 'sslmode=require' for psycopg2 if needed
    # psycopg2 expects 'sslmode', asyncpg expects 'ssl'
    # Since _sanitize_database_url converts to 'ssl', we need to check if we are using psycopg2
    if "postgresql" in database_url and "asyncpg" not in database_url:
        if "ssl=require" in database_url:
            database_url = database_url.replace("ssl=require", "sslmode=require")
        elif "ssl=disable" in database_url:
            database_url = database_url.replace("ssl=disable", "sslmode=disable")
        elif "ssl=allow" in database_url:
            database_url = database_url.replace("ssl=allow", "sslmode=allow")
        elif "ssl=prefer" in database_url:
            database_url = database_url.replace("ssl=prefer", "sslmode=prefer")
        elif "ssl=verify-ca" in database_url:
            database_url = database_url.replace("ssl=verify-ca", "sslmode=verify-ca")
        elif "ssl=verify-full" in database_url:
            database_url = database_url.replace("ssl=verify-full", "sslmode=verify-full")

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
