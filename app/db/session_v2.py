# app/db/session_v2.py
"""
The new asynchronous session maker and dependency provider for Reality Kernel v2.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .engine_v2 import get_async_engine

# Create a configured "AsyncSession" class.
# We will use this to create session instances.
AsyncSessionLocal = async_sessionmaker(
    bind=get_async_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """
    FastAPI dependency provider for getting an async database session.
    This will be the single source of truth for sessions in the new architecture.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
