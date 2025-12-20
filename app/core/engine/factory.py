"""
Factory

هذا الملف جزء من مشروع CogniForge.
"""

import copy
import logging
import os
from typing import Any

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.engine.exceptions import FatalEngineError
from app.core.engine.naming import QuantumStatementNameGenerator
from app.core.engine.pooler import AdaptivePoolerDetector
from app.core.engine.types import DatabaseType, PoolerType
from app.core.engine.url_tools import DatabaseURLSanitizer

logger = logging.getLogger(__name__)


def create_unified_async_engine(
    database_url: str | None = None, echo: bool = False, **kwargs: Any
) -> AsyncEngine:
    """
    🚀 QUANTUM ASYNC ENGINE FACTORY v4.0

    The Single Source of Truth for creating Async SQLAlchemy Engines with
    SUPERHUMAN intelligence for handling PgBouncer, Supabase Pooler, and
    any transaction-pooling middleware.

    Args:
        database_url: The DB connection string. Defaults to os.getenv("DATABASE_URL").
        echo: Whether to log SQL statements.
        **kwargs: Additional arguments passed to create_async_engine.

    Returns:
        AsyncEngine configured for maximum reliability and PgBouncer compatibility.

    Raises:
        FatalEngineError: If critical security settings cannot be applied.
    """
    # --- Phase 1: URL Resolution & Sanitization ---
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    database_url = DatabaseURLSanitizer.sanitize(database_url, for_async=True)

    # --- Phase 2: Intelligent Database Type Detection ---
    db_type = _detect_database_type(database_url)

    # --- Phase 3: Adaptive Pooler Detection ---
    pooler_type = AdaptivePoolerDetector.detect(database_url)

    logger.info(
        f"🧠 Quantum Engine Factory: DB={db_type.name}, Pooler={pooler_type.name}"
    )

    # --- Phase 4: Deep Copy kwargs for Immutability ---
    engine_kwargs = copy.deepcopy(kwargs)
    engine_kwargs["echo"] = echo

    # --- Phase 5: Pool Class Hygiene ---
    pool_class = engine_kwargs.get("poolclass")
    if pool_class == pool.NullPool:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)
        logger.info("🔧 NullPool detected: Removed incompatible pool settings")

    # --- Phase 6: Database-Specific Configuration ---
    if db_type == DatabaseType.POSTGRESQL:
        database_url, engine_kwargs = _configure_postgres_engine(
            database_url, engine_kwargs, pooler_type, pool_class
        )
    elif db_type == DatabaseType.SQLITE:
        database_url, engine_kwargs = _configure_sqlite_engine(
            database_url, engine_kwargs
        )

    # --- Phase 7: Security Validation ---
    if db_type == DatabaseType.POSTGRESQL:
        _validate_postgres_security(engine_kwargs)

    # --- Phase 8: Engine Creation with Event Listeners ---
    engine = create_async_engine(database_url, **engine_kwargs)

    logger.info(
        f"✅ Quantum Async Engine created successfully | "
        f"DB: {db_type.name} | Pooler: {pooler_type.name}"
    )

    return engine


def create_unified_sync_engine(
    database_url: str | None = None, echo: bool = False, **kwargs: Any
) -> Engine:
    """
    🔄 QUANTUM SYNC ENGINE FACTORY

    The Single Source of Truth for creating Sync SQLAlchemy Engines.
    Used for:
    - Alembic Migrations (when run synchronously)
    - Legacy synchronous scripts
    - Administrative operations
    """
    # --- Phase 1: URL Resolution ---
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    database_url = DatabaseURLSanitizer.sanitize(database_url, for_async=True)

    # --- Phase 2: Driver Conversion (async -> sync) ---
    if "postgresql+asyncpg" in database_url:
        database_url = database_url.replace("postgresql+asyncpg", "postgresql")
        logger.debug("🔧 Converted asyncpg to sync driver")

    # --- Phase 3: SSL Parameter Reversal for psycopg2 ---
    database_url = DatabaseURLSanitizer.reverse_ssl_for_sync(database_url)

    # --- Phase 4: Engine Configuration ---
    engine_kwargs = copy.deepcopy(kwargs)
    engine_kwargs["echo"] = echo

    db_type = _detect_database_type(database_url)

    # Pool class hygiene
    pool_class = engine_kwargs.get("poolclass")
    if pool_class == pool.NullPool:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_pre_ping", None)

    if db_type == DatabaseType.POSTGRESQL and pool_class != pool.NullPool:
        engine_kwargs.setdefault("pool_pre_ping", True)
    elif db_type == DatabaseType.SQLITE:
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        if "connect_args" not in engine_kwargs:
            engine_kwargs["connect_args"] = {}
        engine_kwargs["connect_args"]["check_same_thread"] = False

    logger.info(f"🔄 Creating Sync Engine for {db_type.name}")
    return create_engine(database_url, **engine_kwargs)


def _detect_database_type(url: str) -> DatabaseType:
    """Detect the database type from URL."""
    url_lower = url.lower()
    if "postgresql" in url_lower or "postgres" in url_lower:
        return DatabaseType.POSTGRESQL
    elif "sqlite" in url_lower:
        return DatabaseType.SQLITE
    return DatabaseType.UNKNOWN


def _configure_postgres_engine(
    database_url: str,
    engine_kwargs: dict[str, Any],
    pooler_type: PoolerType,
    pool_class: type | None,
) -> tuple[str, dict[str, Any]]:
    """
    🔧 POSTGRESQL ENGINE CONFIGURATION

    Applies the Multi-Level Prepared Statement Shield (MLPSS) and
    other PostgreSQL-specific optimizations.
    """
    # Enforce correct async driver
    if (
        "asyncpg" not in database_url
        and "postgresql://" in database_url
        and "+" not in database_url
    ):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        logger.debug("🔧 Auto-upgraded to postgresql+asyncpg://")

    # Ensure connect_args exists
    if "connect_args" not in engine_kwargs:
        engine_kwargs["connect_args"] = {}

    connect_args = engine_kwargs["connect_args"]

    # =========================================================================
    # 🛡️ MULTI-LEVEL PREPARED STATEMENT SHIELD (MLPSS)
    # =========================================================================

    # LEVEL 1: Disable asyncpg's native prepared statement cache
    connect_args["statement_cache_size"] = 0

    # LEVEL 2: Disable SQLAlchemy asyncpg dialect's prepared statement cache
    connect_args["prepared_statement_cache_size"] = 0

    # LEVEL 3: Quantum-Safe Statement Name Generator
    connect_args["prepared_statement_name_func"] = (
        QuantumStatementNameGenerator.get_generator_func()
    )

    # LEVEL 4: Command Timeout Protection
    connect_args.setdefault("command_timeout", 60)

    # LEVEL 5: Connection Lifetime Management
    connect_args.setdefault("server_settings", {})

    # =========================================================================
    # 🔄 SELF-HEALING CONNECTION POOL CONFIGURATION
    # =========================================================================

    if pool_class != pool.NullPool:
        # Enable connection health checks before use
        engine_kwargs.setdefault("pool_pre_ping", True)

        # Optimal pool sizing for web applications
        engine_kwargs.setdefault("pool_size", 20)
        engine_kwargs.setdefault("max_overflow", 10)

        # Recycle connections to prevent stale connections
        engine_kwargs.setdefault("pool_recycle", 300)

        # Timeout for acquiring connections from pool
        engine_kwargs.setdefault("pool_timeout", 30)

    logger.info(
        f"🛡️ MLPSS Activated | "
        f"statement_cache=0, prepared_stmt_cache=0, "
        f"quantum_naming=enabled, pooler={pooler_type.name}"
    )

    return database_url, engine_kwargs


def _configure_sqlite_engine(
    database_url: str, engine_kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """
    🔧 SQLITE ENGINE CONFIGURATION

    Applies SQLite-specific settings for async operation.
    """
    # Remove incompatible pool settings
    engine_kwargs.pop("pool_size", None)
    engine_kwargs.pop("max_overflow", None)
    engine_kwargs.pop("pool_pre_ping", None)

    # Ensure proper async sqlite protocol
    if "sqlite+aiosqlite" not in database_url and "sqlite://" in database_url:
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

    # Enable cross-thread access for FastAPI/Starlette
    if "connect_args" not in engine_kwargs:
        engine_kwargs["connect_args"] = {}
    engine_kwargs["connect_args"]["check_same_thread"] = False

    logger.info("🔧 SQLite engine configured for async operation")

    return database_url, engine_kwargs


def _validate_postgres_security(engine_kwargs: dict[str, Any]) -> None:
    """
    🔐 SECURITY VALIDATION

    Performs strict validation to ensure all security settings are correctly applied.
    """
    connect_args = engine_kwargs.get("connect_args", {})

    # Validate Level 1: asyncpg statement cache
    if connect_args.get("statement_cache_size") != 0:
        raise FatalEngineError(
            "🚨 SECURITY VIOLATION: statement_cache_size must be 0 for PgBouncer compatibility. "
            f"Current value: {connect_args.get('statement_cache_size')}"
        )

    # Validate Level 2: SQLAlchemy dialect prepared statement cache
    if connect_args.get("prepared_statement_cache_size") != 0:
        raise FatalEngineError(
            "🚨 SECURITY VIOLATION: prepared_statement_cache_size must be 0 for PgBouncer compatibility. "
            f"Current value: {connect_args.get('prepared_statement_cache_size')}"
        )

    # Validate Level 3: Quantum statement name generator
    if "prepared_statement_name_func" not in connect_args:
        raise FatalEngineError(
            "🚨 SECURITY VIOLATION: prepared_statement_name_func is not set. "
            "This is required for collision-free prepared statement naming."
        )

    # Validate the name function produces unique values
    name_func = connect_args["prepared_statement_name_func"]
    test_names = {name_func() for _ in range(10)}
    if len(test_names) != 10:
        raise FatalEngineError(
            "🚨 SECURITY VIOLATION: prepared_statement_name_func does not produce unique names. "
            "This could cause prepared statement collisions."
        )

    logger.debug("✅ Security validation passed")
