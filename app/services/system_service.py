# app/services/system_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class SystemService:
    async def check_database_status(self, db: AsyncSession) -> str:
        try:
            await db.execute(text("SELECT 1"))
            return "healthy"
        except Exception:
            return "unhealthy"

system_service = SystemService()
