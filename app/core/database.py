import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.engine_factory import create_unified_async_engine

logger = logging.getLogger(__name__)

# --- SINGLETON ENGINE CREATION ---
# We strictly use the factory. No raw create_async_engine calls allowed.
engine = create_unified_async_engine()

# --- SESSION FACTORY ---
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for backward compatibility / preference
AsyncSessionLocal = async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.
    Ensures sessions are closed after use.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
