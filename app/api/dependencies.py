"""
API Dependencies Module

Provides dependency injection for API routes.
Uses the unified database layer from app.core.database.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an ASYNC database session for API request handling.
    This is the primary dependency for FastAPI async routes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
