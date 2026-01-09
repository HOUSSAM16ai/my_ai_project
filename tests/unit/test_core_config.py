import os
import pytest
from pydantic import ValidationError
from unittest.mock import patch
from app.core.config import BaseServiceSettings, AppSettings, get_settings

def test_base_settings_defaults():
    """Test that BaseServiceSettings has correct defaults."""
    with patch.dict(os.environ, {}, clear=True):
        settings = BaseServiceSettings(SECRET_KEY="test_secret_key_at_least_32_chars_long_enough")
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False
        assert settings.API_V1_STR == "/api/v1"
        assert settings.DB_POOL_SIZE == 40

def test_base_settings_environment_detection():
    """Test environment detection logic."""
    env_vars = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "prod_secret_key_at_least_32_chars_long_enough",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db"
    }
    with patch.dict(os.environ, env_vars, clear=True):
        settings = BaseServiceSettings()
        assert settings.is_production is True

def test_app_settings_inheritance():
    """Test that AppSettings correctly inherits from BaseServiceSettings."""
    with patch.dict(os.environ, {}, clear=True):
        settings = AppSettings(SECRET_KEY="test_secret_key_at_least_32_chars_long_enough")
        assert settings.PROJECT_NAME == "CogniForge"
        # Check inherited field
        assert settings.ENVIRONMENT == "development"

def test_production_security_enforcement():
    """Test that production security checks are enforced."""
    # Test case: Missing SECRET_KEY
    env_vars_no_secret = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db"
    }
    with patch.dict(os.environ, env_vars_no_secret, clear=True):
        with pytest.raises(ValidationError) as excinfo:
            BaseServiceSettings()
        assert "SECRET_KEY" in str(excinfo.value)

    # Test case: Missing DATABASE_URL
    env_vars_no_db = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "prod_secret_key_at_least_32_chars_long_enough"
    }
    with patch.dict(os.environ, env_vars_no_db, clear=True):
        with pytest.raises(ValidationError) as excinfo:
            BaseServiceSettings()
        assert "DATABASE_URL" in str(excinfo.value)

def test_auto_healing_database_url():
    """Test the database URL auto-healing logic."""
    # Postgres Sync -> Async
    url = "postgresql://user:pass@localhost/db"
    settings = BaseServiceSettings(DATABASE_URL=url, SECRET_KEY="test")
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"

    # SSL Mode handling
    url_ssl = "postgresql://user:pass@localhost/db?sslmode=require"
    settings = BaseServiceSettings(DATABASE_URL=url_ssl, SECRET_KEY="test")
    assert "ssl=require" in settings.DATABASE_URL
