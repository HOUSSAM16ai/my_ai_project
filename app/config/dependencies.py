# app/config/dependencies.py
from .settings import AppSettings
from .settings import get_settings as get_cached_settings


def get_settings() -> AppSettings:
    """
    Dependency injection entry point for accessing application settings.

    This function serves as a framework-agnostic way to obtain the application's
    configuration. It simply returns the cached AppSettings singleton.

    This will be used later by FastAPI's dependency injection system, but it
    contains no FastAPI-specific code, making it safe to import anywhere.

    Returns:
        AppSettings: The singleton application settings object.
    """
    return get_cached_settings()
