"""
Application Service Implementations
Concrete implementations of application service interfaces.
"""

from app.domain.repositories import DatabaseRepository, UserRepository

class DefaultHealthCheckService:
    """Default health check service implementation."""

    def __init__(self, db_repository: DatabaseRepository):
        self._db_repository = db_repository

    async def check_system_health(self) -> dict[str, Any]:
        """Check overall system health."""
        db_health = await self.check_database_health()
        return {
            "status": "healthy" if db_health["connected"] else "unhealthy",
            "database": db_health,
        }

    async def check_database_health(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            is_connected = await self._db_repository.check_connection()
            return {
                "connected": is_connected,
                "status": "ok" if is_connected else "error",
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "error": str(e),
            }

class DefaultSystemService:
    """Default system operations service implementation."""

    def __init__(self, db_repository: DatabaseRepository):
        self._db_repository = db_repository

    async def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return {
            "name": "CogniForge",
            "version": "v4.0",
            "status": "operational",
        }

    async def verify_integrity(self) -> dict[str, Any]:
        """Verify system integrity."""
        db_ok = await self._db_repository.check_connection()
        return {
            "database": db_ok,
            "overall": db_ok,
        }

class DefaultUserService:
    """Default user management service implementation."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
        }

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user."""
        user = await self._user_repository.find_by_email(email)
        if not user:
            return None
        # Simplified - in real implementation, verify password hash
        return {
            "id": user.id,
            "email": user.email,
        }

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Create new user."""
        user = await self._user_repository.create(user_data)
        return {
            "id": user.id,
            "email": user.email,
        }
