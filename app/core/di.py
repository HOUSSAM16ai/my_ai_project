# app/core/di.py

from app.config.settings import get_settings as _get_settings
from app.core.cli_logging import create_logger
from app.core.cli_session import get_session_factory

_settings_singleton = None
_session_factory_singleton = None


def get_settings(env: str | None = None):
    global _settings_singleton
    if _settings_singleton is None:
        if env:
            _settings_singleton = _get_settings()
        else:
            _settings_singleton = _get_settings()
    return _settings_singleton


def get_session():
    global _session_factory_singleton
    if _session_factory_singleton is None:
        settings = get_settings()
        _session_factory_singleton = get_session_factory(settings.DATABASE_URL)
    return _session_factory_singleton


def get_logger(settings=None):
    settings = settings or get_settings()
    return create_logger(settings)
