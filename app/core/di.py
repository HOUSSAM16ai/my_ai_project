from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings as _get_settings_config
from app.core.database import async_session_factory
from app.core.kernel_v2.logging_spine import get_logger as _get_logger

# --- DEPENDENCY INJECTION LAYER ---
# This module decouples the application from specific implementations.
# It currently delegates to the singletons in app.core.database and app.config.settings.

_settings_singleton = _get_settings_config()
_session_factory_singleton = async_session_factory


def get_di_settings() -> AppSettings:
    return _settings_singleton


# Re-export or Alias for consumers expecting 'get_settings' from di
get_settings = get_di_settings


def get_di_session_factory() -> Callable[[], AsyncSession]:
    """Returns the global async session factory."""
    return _session_factory_singleton


async def get_di_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection compliant database session provider.
    """
    async with _session_factory_singleton() as session:
        yield session


# Alias for consumers expecting 'get_session' or 'get_db'
get_session = get_di_db
get_db = get_di_db

# Logging
get_logger = _get_logger
