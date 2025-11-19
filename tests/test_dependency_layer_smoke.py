# tests/test_dependency_layer_smoke.py
import logging
import os

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import AppSettings
from app.core import di
from app.core.di import get_logger, get_session, get_settings


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Fixture to reset the singleton instances in the di module before each test.
    This is crucial for test isolation.
    """
    di._settings_singleton = None
    di._session_factory_singleton = None
    yield


@pytest.fixture(scope="module")
def setup_test_environment():
    """
    Set up a controlled environment for the smoke test.
    """
    # Set a specific database URL for testing. Using an in-memory SQLite database
    # is a fast and isolated way to test database connectivity.
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # Set a known log level for verification.
    os.environ["LOG_LEVEL"] = "DEBUG"
    # Ensure a secret key is provided, as it's a required setting.
    os.environ["SECRET_KEY"] = "test-secret-key-for-smoke-test"

    yield

    # Teardown: Unset the environment variables to avoid side effects on other tests.
    del os.environ["DATABASE_URL"]
    del os.environ["LOG_LEVEL"]
    del os.environ["SECRET_KEY"]


def test_get_logger_smoke(setup_test_environment):
    """
    Smoke test for the get_logger function.

    Verifies that:
    - The function returns a valid logger instance.
    - The logger's level is correctly configured from settings.
    """
    # The logger name is now set by the app, not passed to the DI function
    logger = get_logger()

    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG
    # The name is hardcoded in the cli_logging module
    assert logger.name == "cogniforge.cli"


def test_get_settings_smoke(setup_test_environment):
    """
    Smoke test for the get_settings function.

    Verifies that:
    - The function returns the correct AppSettings object.
    - The settings object has the values from the test environment.
    """
    settings = get_settings()

    assert isinstance(settings, AppSettings)
    assert settings.DATABASE_URL == "sqlite:///:memory:"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.SECRET_KEY == "test-secret-key-for-smoke-test"


def test_get_session_smoke(setup_test_environment):
    """
    Smoke test for the get_session function.

    Verifies that:
    - The function returns a functioning SQLAlchemy session.
    - The session can connect to the database and execute a query.
    """
    session = get_session()

    assert isinstance(session, Session)

    try:
        # Execute a simple query to confirm the session is live.
        result = session.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    finally:
        # It's crucial to close the session to release the connection.
        session.close()
