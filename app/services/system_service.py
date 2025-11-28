# app/services/system_service.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SystemService:
    async def check_database_status(self, db: AsyncSession) -> str:
        try:
            await db.execute(text("SELECT 1"))
            return "healthy"
        except Exception:
            return "unhealthy"

    async def is_database_connected(self, db: AsyncSession) -> bool:
        """Checks if the database is connected."""
        status = await self.check_database_status(db)
        return status == "healthy"


system_service = SystemService()
