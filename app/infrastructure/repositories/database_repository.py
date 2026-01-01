"""
SQLAlchemy Database Repository Implementation
Implements DatabaseRepository interface from domain layer.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyDatabaseRepository:
    """SQLAlchemy implementation of DatabaseRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def check_connection(self) -> bool:
        """Check if database connection is alive."""
        try:
            await self._session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
