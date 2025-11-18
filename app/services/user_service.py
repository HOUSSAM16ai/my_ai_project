# app/services/user_service.py
"""
User Service - A framework-agnostic, DI-enabled service for user management.

This service is responsible for all user-related business logic, including
creation, retrieval, and administrative tasks. It is designed to be completely
decoupled from any web framework and relies on dependency injection for its
database session and application settings.

Thread-Safety: This service is stateless and therefore thread-safe. New
instances can be created per request or shared across threads without issue.
"""

from __future__ import annotations

from logging import Logger
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.di import get_logger, get_session, get_settings
from app.models import User

if TYPE_CHECKING:
    pass


class UserService:
    """A service for user-related operations."""

    def __init__(self, session: Session, settings: Settings, logger: Logger):
        self.session = session
        self.settings = settings
        self.logger = logger

    def get_all_users(self) -> list[User]:
        """Retrieves all users from the database."""
        return self.session.scalars(select(User).order_by(User.id)).all()

    def create_new_user(
        self, full_name: str, email: str, password: str, is_admin: bool = False
    ) -> dict[str, str]:
        """Creates a new user. Returns a dict with status and message."""
        if self.session.scalar(select(User).filter_by(email=email)):
            self.logger.warning(f"Attempted to create user with existing email: {email}")
            return {"status": "error", "message": f"User with email '{email}' already exists."}

        try:
            new_user = User(full_name=full_name, email=email, is_admin=is_admin)
            new_user.set_password(password)
            self.session.add(new_user)
            self.session.commit()
            admin_status = " (Admin)" if is_admin else ""
            self.logger.info(f"User '{full_name}' created with ID {new_user.id}{admin_status}.")
            return {
                "status": "success",
                "message": f"User '{full_name}' created with ID {new_user.id}{admin_status}.",
            }
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating new user: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def ensure_admin_user_exists(self) -> dict[str, str]:
        """
        Ensures the admin user from settings exists and is an admin.
        Returns a dict with status and message.
        """
        admin_email = self.settings.ADMIN_EMAIL
        admin_password = self.settings.ADMIN_PASSWORD
        admin_name = self.settings.ADMIN_NAME

        if not all([admin_email, admin_password, admin_name]):
            self.logger.error("Admin environment variables not set.")
            return {"status": "error", "message": "Admin environment variables not set."}

        try:
            user = self.session.scalar(select(User).filter_by(email=admin_email))
            if user:
                if user.is_admin:
                    return {
                        "status": "success",
                        "message": f"Admin user '{admin_email}' already configured.",
                    }

                user.is_admin = True
                self.session.commit()
                self.logger.info(f"User '{admin_email}' promoted to admin.")
                return {"status": "success", "message": f"User '{admin_email}' promoted to admin."}

            new_admin = User(full_name=admin_name, email=admin_email, is_admin=True)
            new_admin.set_password(admin_password)
            self.session.add(new_admin)
            self.session.commit()
            self.logger.info(f"Admin user '{admin_email}' created.")
            return {"status": "success", "message": f"Admin user '{admin_email}' created."}
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error ensuring admin user exists: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}


# ======================================================================================
# ==                            DEPENDENCY INJECTION FACTORY                          ==
# ======================================================================================

_user_service_singleton = None


def get_user_service() -> UserService:
    """Factory function to get the singleton instance of the UserService."""
    global _user_service_singleton
    if _user_service_singleton is None:
        _user_service_singleton = UserService(
            session=get_session()(),  # get_session returns a factory
            settings=get_settings(),
            logger=get_logger(),
        )
    return _user_service_singleton


# ======================================================================================
# ==                         BACKWARD COMPATIBILITY ADAPTERS                          ==
# ======================================================================================


def get_all_users() -> list[User]:
    """Deprecated: replaced by UserService.get_all_users."""
    return get_user_service().get_all_users()


def create_new_user(
    full_name: str, email: str, password: str, is_admin: bool = False
) -> dict[str, str]:
    """Deprecated: replaced by UserService.create_new_user."""
    return get_user_service().create_new_user(full_name, email, password, is_admin)


def ensure_admin_user_exists() -> dict[str, str]:
    """Deprecated: replaced by UserService.ensure_admin_user_exists."""
    return get_user_service().ensure_admin_user_exists()
