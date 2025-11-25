# tests/test_settings_smoke.py
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.settings import get_settings


@pytest.fixture(scope="function", autouse=True)
def clear_lru_cache():
    """
    Fixture to clear the lru_cache for get_settings before each test function.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_validation_error_on_missing_required_fields():
    """
    SMOKE TEST: Verifies that Pydantic raises a ValidationError if required fields are missing.
    """
    # Create an empty temporary .env file
    empty_env_path = os.path.join(os.path.dirname(__file__), "empty.env")
    with open(empty_env_path, "w") as f:
        f.write("")

    # Patch os.environ to be empty to ensure no env vars are picked up
    with (
        patch.dict(os.environ, {}, clear=True),
        patch(
            "app.config.settings.AppSettings.model_config",
            {"env_file": empty_env_path, "extra": "ignore"},
        ),
    ):
        with pytest.raises(ValidationError) as excinfo:
            # The validation error should be triggered here
            get_settings()

        # Check that the error message contains the names of the missing required fields
        error_str = str(excinfo.value)
        # DATABASE_URL has a default fallback, so it won't be missing
        assert "SECRET_KEY" in error_str
        assert "Field required" in error_str

    if os.path.exists(empty_env_path):
        os.remove(empty_env_path)
