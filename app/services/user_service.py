"""
User Service - A framework-agnostic, DI-enabled service for user management.

This service is responsible for all user-related business logic, including
creation, retrieval, and administrative tasks. It supports both:
1. Dependency injection of an async session (for FastAPI Depends)
2. Standalone usage with async_session_factory (for CLI/scripts)

Thread-Safety: This service is stateless and therefore thread-safe. New
instances can be created per request or shared across threads without issue.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings
from app.core.database import async_session_factory
from app.models import User

if TYPE_CHECKING:
    pass
logger = logging.getLogger(__name__)


class UserService:
    """A service for user-related operations using async database sessions."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        settings: AppSettings | None = None,
        _logger: logging.Logger | None = None,
    ):
        """
        Initialize UserService.

        Args:
            session: Optional AsyncSession. If provided, uses it directly.
                     If None, creates sessions via async_session_factory.
            settings: Optional AppSettings. If None, uses get_settings().
            _logger: Optional logger (ignored, uses module logger).
        """
        self._injected_session = session
        self.settings = settings or get_settings()

    async def _get_session(self):
        """Returns the session to use - either injected or create new one."""
        if self._injected_session is not None:
            return self._injected_session
        return None

    async def get_all_users(self) -> list[User]:
        """Retrieves all users from the database."""
        if self._injected_session is not None:
            result = await self._injected_session.execute(
                select(User).order_by(User.id)
            )
            return list(result.scalars().all())
        async with async_session_factory() as session:
            result = await session.execute(select(User).order_by(User.id))
            return list(result.scalars().all())

    async def create_new_user(
        self, full_name: str, email: str, password: str, is_admin: bool = False
    ) -> dict[str, str]:
        """Creates a new user. Returns a dict with status and message."""
        if self._injected_session is not None:
            return await self._create_new_user_with_session(
                self._injected_session, full_name, email, password, is_admin
            )
        async with async_session_factory() as session:
            return await self._create_new_user_with_session(
                session, full_name, email, password, is_admin
            )

    async def _create_new_user_with_session(
        self,
        session: AsyncSession,
        full_name: str,
        email: str,
        password: str,
        is_admin: bool,
    ) -> dict[str, str]:
        """Internal method to create user with a specific session."""
        result = await session.execute(select(User).filter_by(email=email))
        if result.scalar():
            logger.warning(f"Attempted to create user with existing email: {email}")
            return {
                "status": "error",
                "message": f"User with email '{email}' already exists.",
            }
        try:
            new_user = User(full_name=full_name, email=email, is_admin=is_admin)
            new_user.set_password(password)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            admin_status = " (Admin)" if is_admin else ""
            logger.info(
                f"User '{full_name}' created with ID {new_user.id}{admin_status}."
            )
            return {
                "status": "success",
                "message": f"User '{full_name}' created with ID {new_user.id}{admin_status}.",
            }
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating new user: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def ensure_admin_user_exists(self) -> dict[str, str]:
        """
        Ensures the admin user from settings exists and is an admin.
        Returns a dict with status and message.
        """
        admin_email = self.settings.ADMIN_EMAIL
        admin_password = self.settings.ADMIN_PASSWORD
        admin_name = self.settings.ADMIN_NAME
        if not all([admin_email, admin_password, admin_name]):
            logger.error("Admin environment variables not set.")
            return {
                "status": "error",
                "message": "Admin environment variables not set.",
            }
        if self._injected_session is not None:
            return await self._ensure_admin_with_session(
                self._injected_session, admin_email, admin_password, admin_name
            )
        async with async_session_factory() as session:
            return await self._ensure_admin_with_session(
                session, admin_email, admin_password, admin_name
            )

    async def _ensure_admin_with_session(
        self,
        session: AsyncSession,
        admin_email: str,
        admin_password: str,
        admin_name: str,
    ) -> dict[str, str]:
        """Internal method to ensure admin exists with a specific session."""
        try:
            result = await session.execute(select(User).filter_by(email=admin_email))
            user = result.scalar()
            if user:
                if user.is_admin:
                    return {
                        "status": "success",
                        "message": f"Admin user '{admin_email}' already configured.",
                    }
                user.is_admin = True
                await session.commit()
                logger.info(f"User '{admin_email}' promoted to admin.")
                return {
                    "status": "success",
                    "message": f"User '{admin_email}' promoted to admin.",
                }
            new_admin = User(full_name=admin_name, email=admin_email, is_admin=True)
            new_admin.set_password(admin_password)
            session.add(new_admin)
            await session.commit()
            logger.info(f"Admin user '{admin_email}' created.")
            return {
                "status": "success",
                "message": f"Admin user '{admin_email}' created.",
            }
        except Exception as e:
            await session.rollback()
            logger.error(f"Error ensuring admin user exists: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}


_user_service_singleton: UserService | None = None


def get_user_service() -> UserService:
    """
    Factory function to get the singleton instance of the UserService.

    Note: This singleton is safe because UserService without an injected session
    creates a new session via async_session_factory for each operation.
    This ensures proper session lifecycle management.
    """
    global _user_service_singleton
    if _user_service_singleton is None:
        _user_service_singleton = UserService()
    return _user_service_singleton


async def get_all_users_async() -> list[User]:
    """Async function to get all users."""
    return await get_user_service().get_all_users()


async def create_new_user_async(
    full_name: str, email: str, password: str, is_admin: bool = False
) -> dict[str, str]:
    """Async function to create a new user."""
    return await get_user_service().create_new_user(
        full_name, email, password, is_admin
    )
