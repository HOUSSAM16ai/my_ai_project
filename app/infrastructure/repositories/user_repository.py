"""
SQLAlchemy User Repository Implementation
Implements UserRepository interface from domain layer.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.models import User

class SQLAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, user_id: int) -> User | None:
        """Find user by ID."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        result = await self._session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: dict[str, Any]) -> User:
        """Create new user."""
        user = User(**user_data)
        self._session.add(user)
        await self._session.flush()
        return user

    async def update(self, user_id: int, user_data: dict[str, Any]) -> User | None:
        """Update user."""
        user = await self.find_by_id(user_id)
        if not user:
            return None
        for key, value in user_data.items():
            setattr(user, key, value)
        await self._session.flush()
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        user = await self.find_by_id(user_id)
        if not user:
            return False
        await self._session.delete(user)
        await self._session.flush()
        return True
