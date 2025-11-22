from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import async_session_factory

# --- DEPENDENCY INJECTION LAYER ---
# This module decouples the application from specific implementations.
# It currently delegates to the singletons in app.core.database and app.core.config.

_settings_singleton = get_settings()
_session_factory_singleton = async_session_factory

def get_di_settings() -> Settings:
    return _settings_singleton

def get_di_session_factory() -> Callable[[], AsyncSession]:
    """Returns the global async session factory."""
    return _session_factory_singleton

async def get_di_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection compliant database session provider.
    """
    async with _session_factory_singleton() as session:
        yield session
