"""
Dependency Injection Container and Facade.
------------------------------------------
This module acts as the central registry for dependencies (DIP) and provides
facade functions for legacy/core components to maintain backward compatibility.

It combines the new 'Container' for SOLID refactoring with re-exports of
existing core services.
"""

from collections.abc import Callable
from typing import Annotated, Any, ClassVar, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# --- Legacy / Core Re-exports ---
from app.core.config import get_settings
from app.core.database import get_db
from app.core.database import get_db as get_session  # Alias for backward compatibility
from app.core.logging import get_logger

# --- Facade Functions for Legacy Routers ---


def get_system_service():
    from app.services.system.system_service import system_service

    return system_service


async def get_health_check_service(db: Annotated[AsyncSession, Depends(get_db)]):
    from app.application.services import DefaultHealthCheckService
    from app.infrastructure.repositories.database_repository import SQLAlchemyDatabaseRepository

    repo = SQLAlchemyDatabaseRepository(db)
    return DefaultHealthCheckService(repo)


# --- New DI Container (SOLID) ---

T = TypeVar("T")


class Container:
    """
    A simple Dependency Injection Container to enforce DIP (Dependency Inversion Principle).
    """

    _factories: ClassVar[dict[type, Callable[[], Any]]] = {}
    _singletons: ClassVar[dict[type, Any]] = {}

    @classmethod
    def register(cls, interface: type[T], factory: Callable[[], T]):
        """
        Register a factory function for a given interface.
        Whenever resolve is called, this factory is executed (Transient).
        """
        cls._factories[interface] = factory

    @classmethod
    def register_singleton(cls, interface: type[T], instance: T):
        """
        Register a specific instance as a Singleton.
        """
        cls._singletons[interface] = instance

    @classmethod
    def register_singleton_factory(cls, interface: type[T], factory: Callable[[], T]):
        """
        Register a factory that is called once, then cached (Lazy Singleton).
        """

        def lazy_wrapper():
            if interface not in cls._singletons:
                cls._singletons[interface] = factory()
            return cls._singletons[interface]

        cls._factories[interface] = lazy_wrapper

    @classmethod
    def resolve(cls, interface: type[T]) -> T:
        """
        Resolve the dependency for the given interface.
        """
        if interface in cls._singletons:
            return cls._singletons[interface]

        if interface in cls._factories:
            return cls._factories[interface]()

        raise ValueError(f"No registration found for {interface.__name__}")

    @classmethod
    def clear(cls):
        """Clear the container (useful for testing)."""
        cls._factories.clear()
        cls._singletons.clear()


# Explicitly export legacy items to satisfy linter regarding "unused import" if they are part of API
__all__ = [
    "Container",
    "get_db",
    "get_health_check_service",
    "get_logger",
    "get_session",
    "get_settings",
    "get_system_service",
]
