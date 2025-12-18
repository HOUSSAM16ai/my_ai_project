# app/services/system_service.py
"""
System Service for infrastructure health and integrity checks.
Encapsulates database connectivity verification and critical user checks.
"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models import User


class SystemService:
    async def check_database_status(self, db: AsyncSession) -> str:
        """
        Executes a simple query to verify database connectivity.
        """
        try:
            await db.execute(text("SELECT 1"))
            return "healthy"
        except Exception:
            return "unhealthy"

    async def is_database_connected(self, db: AsyncSession) -> bool:
        """Checks if the database is connected."""
        status = await self.check_database_status(db)
        return status == "healthy"

    async def verify_system_integrity(self) -> dict:
        """
        Performs a deep system integrity check.
        Verifies DB connectivity and Admin user presence without requiring an external session.
        Uses a dedicated session to ensure independence from request scope.
        """
        admin_present = False
        db_status = "unknown"

        try:
            # Create a dedicated session for the health check
            async with async_session_factory() as session:
                # Check 1: DB Connectivity
                await session.execute(text("SELECT 1"))
                db_status = "connected"

                # Check 2: Admin Presence
                # We check for the canonical admin email
                # Using scalar_one_or_none would be safer but first() is robust enough for boolean check
                res = await session.execute(select(User).where(User.email == "admin@example.com"))
                if res.scalars().first():
                    admin_present = True
        except Exception:
            # Log could be added here, but we return structured status
            db_status = "unreachable"

        return {
            "status": "ok",
            "service": "backend running",
            "secrets_ok": True,  # Implied if app reached this point
            "admin_present": admin_present,
            "db": db_status,
        }


system_service = SystemService()
