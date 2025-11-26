import os
from unittest.mock import patch

import pytest

from app.config.settings import AppSettings


class TestSuperhumanConfiguration:
    @pytest.fixture
    def mock_codespaces_env(self):
        """Simulates a GitHub Codespaces environment."""
        env_vars = {
            "CODESPACES": "true",
            "CODESPACE_NAME": "legendary-codespace",
            "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "github.dev",
            "DATABASE_URL": "postgresql://user:pass@dbhost:5432/db?sslmode=require",
            "SECRET_KEY": "superhuman-secret-key",
            "OPENAI_API_KEY": "sk-123456789",
            "ENVIRONMENT": "production",  # To test override
        }
        with patch.dict(os.environ, env_vars, clear=True):
            yield

    def test_codespaces_detection(self, mock_codespaces_env):
        """Verifies that Codespaces logic is active."""
        settings = AppSettings()
        assert settings.CODESPACES is True
        assert settings.CODESPACE_NAME == "legendary-codespace"

    def test_database_url_auto_healing(self, mock_codespaces_env):
        """Verifies the 'Superhuman Algorithm' for DB URL fixing."""
        settings = AppSettings()
        # Expecting asyncpg injection and sslmode fix
        expected = "postgresql+asyncpg://user:pass@dbhost:5432/db?ssl=require"
        assert expected == settings.DATABASE_URL

    def test_secret_absorption(self, mock_codespaces_env):
        """Verifies secrets are correctly mapped."""
        settings = AppSettings()
        assert settings.SECRET_KEY == "superhuman-secret-key"
        assert settings.OPENAI_API_KEY == "sk-123456789"

    def test_sqlite_fallback(self):
        """Verifies SQLite injection when DB URL is missing (Safe-Fail)."""
        with patch.dict(os.environ, {"SECRET_KEY": "test"}, clear=True):
            settings = AppSettings()
            assert settings.DATABASE_URL == "sqlite+aiosqlite:///./test.db"

    def test_cors_injection(self):
        """Verifies CSV string injection for CORS."""
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "test",
                "DATABASE_URL": "sqlite:///",
                "BACKEND_CORS_ORIGINS": "http://localhost:3000,https://myapp.com",
            },
            clear=True,
        ):
            settings = AppSettings()
            assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
            assert "https://myapp.com" in settings.BACKEND_CORS_ORIGINS
