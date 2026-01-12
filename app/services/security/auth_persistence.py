"""
Authentication Persistence Layer
Encapsulates all Data Access Logic for authentication and user management.
Part of the "Evolutionary Logic Distillation" - separating persistence from orchestration.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User

logger = logging.getLogger(__name__)


class AuthPersistence:
    """
    Encapsulates all Data Access Logic for Authentication.
    Handles database queries for user authentication and registration.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email address (case-insensitive).
        """
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by ID.
        """
        return await self.db.get(User, user_id)

    async def create_user(
        self, full_name: str, email: str, password: str, is_admin: bool = False
    ) -> User:
        """
        Create a new user in the database.
        """
        new_user = User(
            full_name=full_name,
            email=email.lower().strip(),
            is_admin=is_admin,
        )
        new_user.set_password(password)

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def user_exists(self, email: str) -> bool:
        """
        Check if a user with the given email already exists.
        """
        user = await self.get_user_by_email(email)
        return user is not None
