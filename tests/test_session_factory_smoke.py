# tests/test_session_factory_smoke.py

import os

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

# IMPORTANT: We are importing from the new, independent session factory,
# not from anything related to the existing Flask app structure.
from app.db.session_factory import create_session, make_engine

# --- Test Constants ---
TEST_DATABASE_URL = "sqlite:///:memory:"


def test_session_factory_smoke_test():
    """
    A simple smoke test to verify that the session factory can be initialized
    and can execute a basic query without any Flask application context.

    This test ensures the fundamental viability of the session factory for use in
    non-Flask environments like FastAPI, CLI tools, or standalone scripts.

    Steps:
    1. Explicitly create an engine for an in-memory SQLite database.
    2. Use `create_session` to get a new database session bound to this engine.
    3. Execute a `SELECT 1` query.
    4. Assert that the result is `1`.
    5. Ensure the session can be closed.
    """
    # 1. Create a dedicated engine for this test to ensure isolation.
    # This avoids reliance on any global state or environment variables.
    engine = make_engine(TEST_DATABASE_URL)

    # 2. Create a new session using the factory.
    session: Session = create_session(engine)
    assert session is not None, "create_session() should not return None"

    try:
        # 3. Execute a simple, database-agnostic query.
        result = session.execute(text("SELECT 1")).scalar_one()

        # 4. Assert the correctness of the result.
        assert result == 1, f"Expected result of 'SELECT 1' to be 1, but got {result}"

    finally:
        # 5. Ensure the session is closed to release resources.
        session.close()


def test_create_session_respects_environment_variable(monkeypatch):
    """
    Verifies that `create_session` (via its initialization path) correctly
    uses the `DATABASE_URL` from an environment variable if no engine is provided.
    """
    # Use monkeypatch to safely set the environment variable for this test only.
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)

    # We need to reset the global SessionLocal to ensure our env var is used for initialization.
    # This is a bit of a hack, but necessary for testing the initialization path.
    # In a real application, the factory is initialized only once.
    from app.db import session_factory
    session_factory.SessionLocal = None

    session: Session = create_session()
    assert session is not None
    try:
        result = session.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    finally:
        session.close()

    # Clean up the global state after the test.
    session_factory.SessionLocal = None


def test_make_engine_raises_error_if_no_url_provided():
    """
    Ensures that `make_engine` raises a `ValueError` if the `DATABASE_URL`
    is not available in the environment or passed as an argument.
    """
    # Ensure the environment variable is not set.
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    with pytest.raises(ValueError, match="DATABASE_URL is not set"):
        make_engine()
