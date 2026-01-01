"""
Domain Repository Interfaces (Protocols)
Defines contracts for data access following Dependency Inversion Principle.
Domain layer defines interfaces, Infrastructure layer implements them.
"""

from typing import Any, Protocol

class DatabaseRepository(Protocol):
    """Database operations interface."""

    async def check_connection(self) -> bool:
        """Check if database connection is alive."""
        ...

class UserRepository(Protocol):
    """User repository interface."""

    async def find_by_id(self, user_id: int) -> Any | None:
        """Find user by ID."""
        ...

    async def find_by_email(self, email: str) -> Any | None:
        """Find user by email."""
        ...

    async def create(self, user_data: dict[str, Any]) -> dict[str, str | int | bool]:
        """Create new user."""
        ...

    async def update(self, user_id: int, user_data: dict[str, Any]) -> Any | None:
        """Update user."""
        ...

    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        ...
