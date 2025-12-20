"""
Di

هذا الملف جزء من مشروع CogniForge.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings
from app.config.settings import get_settings as _get_settings_config
from app.core.database import async_session_factory
from app.core.kernel_v2.logging_spine import get_logger as _get_logger

_settings_singleton = _get_settings_config()
_session_factory_singleton = async_session_factory


def get_di_settings() -> AppSettings:
    return _settings_singleton


get_settings = get_di_settings


async def get_di_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection compliant database session provider.
    """
    async with _session_factory_singleton() as session:
        yield session


get_session = get_di_db
get_db = get_di_db
get_logger = _get_logger


# Application Service Dependencies (Clean Architecture)
async def get_health_check_service():
    """
    Get HealthCheckService implementation.
    Returns interface, not concrete class (DIP).
    """
    from app.application.services import DefaultHealthCheckService
    from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

    async with _session_factory_singleton() as session:
        db_repo = SQLAlchemyDatabaseRepository(session)
        return DefaultHealthCheckService(db_repo)


async def get_system_service():
    """
    Get SystemService implementation.
    Returns interface, not concrete class (DIP).
    """
    from app.application.services import DefaultSystemService
    from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

    async with _session_factory_singleton() as session:
        db_repo = SQLAlchemyDatabaseRepository(session)
        return DefaultSystemService(db_repo)
