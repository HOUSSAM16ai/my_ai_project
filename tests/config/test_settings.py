# tests/config/test_settings.py
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.settings import AppSettings


def test_database_url_fixer_handles_duplicates_gracefully():
    """
    Tests that the DATABASE_URL validator doesn't create malformed URLs
    when 'sslmode' and 'ssl' parameters are both present or duplicated.
    """
    # This URL is designed to break the simple .replace() logic
    original_url = "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require&ssl=true"

    with patch.dict(os.environ, {"DATABASE_URL": original_url, "SECRET_KEY": "test"}):
        try:
            settings = AppSettings()
            # The corrected URL should have only one 'ssl' parameter.
            # The 'sslmode' should be removed.
            assert "sslmode" not in settings.DATABASE_URL
            assert "ssl=true" not in settings.DATABASE_URL
            assert settings.DATABASE_URL.count("ssl=require") == 1, (
                f"URL should contain 'ssl=require' exactly once. Got: {settings.DATABASE_URL}"
            )
        except ValidationError as e:
            pytest.fail(f"AppSettings validation failed unexpectedly: {e}")


def test_database_url_fixer_handles_simple_sslmode():
    """
    Tests that the DATABASE_URL validator correctly converts a simple 'sslmode=require'.
    """
    original_url = "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require"

    with patch.dict(os.environ, {"DATABASE_URL": original_url, "SECRET_KEY": "test"}):
        try:
            settings = AppSettings()
            assert "sslmode" not in settings.DATABASE_URL
            assert settings.DATABASE_URL.endswith("?ssl=require"), (
                f"URL should end with '?ssl=require'. Got: {settings.DATABASE_URL}"
            )
        except ValidationError as e:
            pytest.fail(f"AppSettings validation failed unexpectedly: {e}")
