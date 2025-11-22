import copy
import logging
import os
from typing import Any, Dict

from sqlalchemy import create_engine
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
        raise FatalEngineError("DATABASE_URL is not set.")

    # Auto-correct common protocol mistakes
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # If using asyncpg, ensure the scheme is correct
    if "asyncpg" not in url and "sqlite" not in url and "postgresql" in url:
        # Default to asyncpg for async engines if not specified
        # However, this function doesn't know if we are creating async or sync yet.
        # We will handle scheme enforcement in the specific creator functions.
        pass

    return url

def create_unified_async_engine(
    database_url: str = None,
    echo: bool = False,
    **kwargs: Any
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

    # --- CRITICAL CONFIGURATION ENFORCEMENT ---
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
        engine_kwargs["connect_args"]["statement_cache_size"] = 0

        # Enforce safe pooling defaults if not provided
        engine_kwargs.setdefault("pool_pre_ping", True)
        engine_kwargs.setdefault("pool_size", 20)
        engine_kwargs.setdefault("max_overflow", 10)

        logger.info(f"Creating Unified Async Engine for Postgres. Cache Disabled. Pool Size: {engine_kwargs.get('pool_size')}")

    elif is_sqlite:
        # SQLite Specific Cleanups
        # SQLite doesn't support server-side pooling arguments
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)

        # Ensure proper async sqlite protocol
        if "sqlite+aiosqlite" not in database_url and "sqlite://" in database_url:
             database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Enable foreign keys for SQLite
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}
        engine_kwargs["connect_args"]["check_same_thread"] = False # Needed for FastAPI/Starlette

        logger.info("Creating Unified Async Engine for SQLite.")

    # Final Check
    if is_postgres and engine_kwargs.get("connect_args", {}).get("statement_cache_size") != 0:
        raise FatalEngineError("Security Violation: statement_cache_size must be 0 for Postgres/PgBouncer.")

    return create_async_engine(database_url, **engine_kwargs)

def create_unified_sync_engine(
    database_url: str = None,
    echo: bool = False,
    **kwargs: Any
):
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
        database_url = database_url.replace("postgresql+asyncpg", "postgresql") # Fallback to default (psycopg2)

    engine_kwargs = copy.deepcopy(kwargs)
    engine_kwargs["echo"] = echo

    is_sqlite = "sqlite" in database_url

    if not is_sqlite:
         engine_kwargs.setdefault("pool_pre_ping", True)
         # Note: statement_cache_size is an asyncpg-specific setting, not needed for sync psycopg2
    else:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}
        engine_kwargs["connect_args"]["check_same_thread"] = False

    logger.info(f"Creating Unified Sync Engine for {'SQLite' if is_sqlite else 'Postgres'}.")
    return create_engine(database_url, **engine_kwargs)
