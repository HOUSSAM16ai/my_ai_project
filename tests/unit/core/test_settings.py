import os
from unittest.mock import patch

import pytest

from app.core.settings.base import (
    AppSettings,
    BaseServiceSettings,
    _normalize_csv_or_list,
    get_settings,
)


class TestCoreConfig:
    """Test suite for the unified configuration system."""

    def test_settings_defaults(self):
        """Verify default settings are correct."""
        settings = get_settings()
        assert settings.SERVICE_NAME == "CogniForge-Core"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False
        assert settings.API_V1_STR == "/api/v1"

    def test_csv_parsing(self):
        """Verify CSV string parsing for lists."""
        assert _normalize_csv_or_list(None) == []
        assert _normalize_csv_or_list("") == []
        assert _normalize_csv_or_list("foo,bar") == ["foo", "bar"]
        assert _normalize_csv_or_list(" foo , bar ") == ["foo", "bar"]
        assert _normalize_csv_or_list(["foo", "bar"]) == ["foo", "bar"]
        assert _normalize_csv_or_list('["foo", "bar"]') == ["foo", "bar"]

    def test_database_url_fallback(self):
        """Verify DB URL fallback logic."""
        # Test default fallback for dev
        with patch.dict(os.environ, {}, clear=True):
             # Force environment to development in logic simulation if needed,
             # but here we rely on defaults or explicit instantiation
             settings = AppSettings(ENVIRONMENT="development", DATABASE_URL=None)
             assert "sqlite" in settings.DATABASE_URL
             assert "dev.db" in settings.DATABASE_URL

    def test_production_security_check(self):
        """Verify production security guardrails."""
        from pydantic import ValidationError

        # Should fail if DEBUG is True in Prod
        with pytest.raises(ValueError, match="DEBUG must be False"):
            BaseServiceSettings(
                SERVICE_NAME="test",
                ENVIRONMENT="production",
                DEBUG=True,
                SECRET_KEY="x" * 64,
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
            )

        # Should fail if weak secret (length) - Enforced globally by Pydantic
        with pytest.raises(ValidationError, match="String should have at least 32 characters"):
            BaseServiceSettings(
                SERVICE_NAME="test",
                ENVIRONMENT="production",
                DEBUG=False,
                SECRET_KEY="weak",
                DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
            )

    def test_base_service_settings(self):
        """Verify BaseServiceSettings works for microservices."""
        settings = BaseServiceSettings(
            SERVICE_NAME="UserService",
            ENVIRONMENT="testing"
        )
        assert settings.SERVICE_NAME == "UserService"
        assert settings.ENVIRONMENT == "testing"
        # Testing usually falls back to in-memory sqlite
        assert ":memory:" in settings.DATABASE_URL
