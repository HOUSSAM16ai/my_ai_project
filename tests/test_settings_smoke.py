# tests/test_settings_smoke.py
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# We have to patch the singleton accessor's cache before importing the AppSettings
# or the get_settings function to ensure our test-specific environment is used.
from app.config.settings import get_settings


@pytest.fixture(scope="function", autouse=True)
def clear_lru_cache():
    """
    Fixture to clear the lru_cache for get_settings before each test function.
    This is crucial to ensure that each test can initialize its own settings.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_load_from_env_file():
    """
    SMOKE TEST: Verifies that AppSettings correctly loads configuration from a .env file.
    """
    # Use a temporary, test-specific .env file
    test_env_path = os.path.join(os.path.dirname(__file__), "temp.env")
    assert os.path.exists(test_env_path), "Test .env file must exist"

    # Patch the model_config to use our specific test .env file
    # AND patch os.environ to avoid interference from conftest.py
    with patch.dict(os.environ, {}, clear=True), patch(
        "app.config.settings.AppSettings.model_config",
        {"env_file": test_env_path, "extra": "ignore"},
    ):
        settings = get_settings()

        assert settings.DATABASE_URL == "postgresql://test:test@localhost:5432/test"
        assert settings.SECRET_KEY == "test-secret-key"
        assert settings.AI_SERVICE_URL == "http://localhost:8080"
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.DEFAULT_AI_MODEL == "test/model"


def test_settings_validation_error_on_missing_required_fields():
    """
    SMOKE TEST: Verifies that Pydantic raises a ValidationError if required fields are missing.
    """
    # Create an empty temporary .env file
    empty_env_path = os.path.join(os.path.dirname(__file__), "empty.env")
    with open(empty_env_path, "w"):
        pass

    # Patch os.environ to be empty to ensure no env vars are picked up
    with patch.dict(os.environ, {}, clear=True), patch(
        "app.config.settings.AppSettings.model_config",
        {"env_file": empty_env_path, "extra": "ignore"},
    ):
        with pytest.raises(ValidationError) as excinfo:
            # The validation error should be triggered here
            get_settings()

        # Check that the error message contains the names of the missing required fields
        error_str = str(excinfo.value)
        assert "DATABASE_URL" in error_str
        assert "Field required" in error_str
        assert "SECRET_KEY" in error_str

    os.remove(empty_env_path)  # Clean up the empty .env file


def test_get_settings_is_a_singleton():
    """
    SMOKE TEST: Verifies that get_settings() returns the same instance on subsequent calls.
    """
    test_env_path = os.path.join(os.path.dirname(__file__), "temp.env")

    # Just verify singleton behavior, env doesn't matter much as long as it's valid
    # We use temp.env so it loads valid settings
    with patch.dict(os.environ, {}, clear=True), patch(
        "app.config.settings.AppSettings.model_config",
        {"env_file": test_env_path, "extra": "ignore"},
    ):
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
        assert id(settings1) == id(settings2)
