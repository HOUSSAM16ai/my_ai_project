import logging
from app.core.database import async_session_factory
from app.config.settings import get_settings as _get_settings
from app.core.cli_logging import create_logger

_settings_singleton = None
_session_factory_singleton = None


def get_settings(env: str | None = None):
    global _settings_singleton
    if _settings_singleton is None:
        _settings_singleton = _get_settings()
    return _settings_singleton


def get_session():
    """
    Returns the Singleton Async Session Factory from app.core.database.
    This ensures we use the ONE TRUE ENGINE created by the Unified Factory.
    """
    # Direct return of the factory from core.database
    # We wrap it in a singleton getter just to maintain the DI interface pattern
    # if we ever need lazy loading (though app.core.database loads at import).
    return async_session_factory

def get_logger():
    """Returns a logger instance."""
    settings = get_settings()
    return create_logger(settings)
