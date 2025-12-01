import logging
from collections.abc import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.core.engine_factory import (
    DatabaseURLSanitizer,
    create_unified_async_engine,
)

logger = logging.getLogger(__name__)

# --- SINGLETON ENGINE CREATION ---
# We strictly use the factory. No raw create_async_engine calls allowed.
engine = create_unified_async_engine()

# --- SESSION FACTORY (ASYNC) ---
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for backward compatibility / preference
AsyncSessionLocal = async_session_factory


# =============================================================================
# 🔧 SYNC SESSION SUPPORT (For Legacy/Background Services)
# =============================================================================
# Some services like master_agent_service.py use synchronous sessions
# for background thread operations. This provides backward compatibility.

_sync_engine = None
_sync_session_factory = None


def _get_sync_engine():
    """Lazily create sync engine only when needed."""
    global _sync_engine
    if _sync_engine is None:
        import os

        db_url = os.getenv("DATABASE_URL")
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)
        # Convert async URL to sync if needed
        if "postgresql+asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")
        elif "sqlite+aiosqlite" in db_url:
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        # Reverse SSL params for psycopg2
        db_url = DatabaseURLSanitizer.reverse_ssl_for_sync(db_url)

        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        _sync_engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    return _sync_engine


def _get_sync_session_factory():
    """Lazily create sync session factory only when needed."""
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=_get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sync_session_factory


class SessionLocal:
    """
    🔧 COMPATIBILITY LAYER FOR SYNC SESSIONS

    This class provides a sync session factory interface that mimics
    the old Flask-SQLAlchemy SessionLocal pattern. It's used by:
    - master_agent_service.py (background threads)
    - Other legacy sync code

    Usage:
        session = SessionLocal()
        try:
            # do work
            session.commit()
        finally:
            session.close()
    """

    def __new__(cls) -> Session:
        """Create and return a new sync session."""
        factory = _get_sync_session_factory()
        return factory()


@contextmanager
def get_sync_session():
    """Context manager for sync sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.
    Ensures sessions are closed after use.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e!s}")
            await session.rollback()
            raise
        finally:
            await session.close()
