"""
Canonical Database Factory for CogniForge.

Provides a unified Factory Pattern for creating AsyncEngines and SessionMakers.
Supports Microservices (Bounded Contexts) by allowing each service to instantiate
its own isolated DB stack based on its configuration.

Standards:
- Async First: Uses `sqlalchemy.ext.asyncio`.
- Factory Pattern: No global state for microservices; explicit `create_engine` calls.
- Connection Pooling: Configured via settings.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings.base import BaseServiceSettings, get_settings

logger = logging.getLogger(__name__)

__all__ = ["create_db_engine", "create_session_factory", "get_db", "engine", "async_session_factory"]

def create_db_engine(settings: BaseServiceSettings) -> AsyncEngine:
    """
    Creates an AsyncEngine based on the provided settings.
    Canonical implementation for all services.
    """
    db_url = settings.DATABASE_URL
    if not db_url:
        raise ValueError("DATABASE_URL is not set in settings.")

    engine_args = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    if "sqlite" in db_url:
        engine_args["connect_args"] = {"check_same_thread": False}
        logger.info(f"🔌 Database (SQLite): {settings.SERVICE_NAME}")
    else:
        # Postgres / Production optimization
        is_dev = settings.ENVIRONMENT in ("development", "testing")

        # Pool size
        engine_args["pool_size"] = 5 if is_dev else 40
        engine_args["max_overflow"] = 10 if is_dev else 60

        # PgBouncer Compatibility (Supabase)
        # Disable prepared statements
        engine_args["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        }
        logger.info(f"🔌 Database (Postgres): {settings.SERVICE_NAME}")

    return create_async_engine(db_url, **engine_args)

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates a configured sessionmaker for the given engine."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

# -----------------------------------------------------------------------------
# Global Singleton (For Legacy App/Core usage only)
# -----------------------------------------------------------------------------
# Ideally, we should remove this, but for Phase 2 backward compatibility, we keep it.
# Services should NOT use this. They should create their own in their `database.py`.

_legacy_settings = get_settings()
engine: AsyncEngine = create_db_engine(_legacy_settings)
async_session_factory = create_session_factory(engine)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting a DB session.
    Used by the Monolith/Core only. Microservices should define their own `get_db`.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
