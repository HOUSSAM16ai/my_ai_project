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

system_service = SystemService()
