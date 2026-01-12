from app.core.settings.base import BaseServiceSettings
from microservices.user_service.settings import UserServiceSettings


def test_base_service_settings_defaults():
    """Test that BaseServiceSettings has correct defaults."""

    class TestSettings(BaseServiceSettings):
        SERVICE_NAME: str = "test-service"
        DATABASE_URL: str = "sqlite:///test.db"

    settings = TestSettings()
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"
    # Auto-fix check
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///test.db"


def test_user_service_settings_inheritance():
    """Test that UserServiceSettings correctly inherits and sets defaults."""
    settings = UserServiceSettings()
    assert settings.SERVICE_NAME == "user-service"
    assert "user_service.db" in settings.DATABASE_URL
    assert isinstance(settings, BaseServiceSettings)


def test_user_service_settings_env_override(monkeypatch):
    """Test that env vars override defaults."""
    monkeypatch.setenv("USER_DEBUG", "True")
    monkeypatch.setenv("USER_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("USER_DATABASE_URL", "sqlite:///env.db")

    # We need to clear cache if we used get_settings, but here we instantiate directly
    settings = UserServiceSettings()
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///env.db"
