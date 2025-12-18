"""
Application Service Interfaces (Protocols)
Defines contracts for application services following Dependency Inversion Principle.
"""

from typing import Any, Protocol


class HealthCheckService(Protocol):
    """Health check service interface."""

    async def check_system_health(self) -> dict[str, Any]:
        """Check overall system health."""
        ...

    async def check_database_health(self) -> dict[str, Any]:
        """Check database connectivity."""
        ...


class SystemService(Protocol):
    """System operations service interface."""

    async def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        ...

    async def verify_integrity(self) -> dict[str, Any]:
        """Verify system integrity."""
        ...


class UserService(Protocol):
    """User management service interface."""

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID."""
        ...

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user."""
        ...

    async def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Create new user."""
        ...
