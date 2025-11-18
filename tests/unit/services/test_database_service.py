# tests/unit/services/test_database_service.py
"""
Unit Tests for the DatabaseService

This test suite focuses on the isolated testing of the DatabaseService class.
It uses an in-memory SQLite database to ensure tests are fast, repeatable,
and do not have external dependencies.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.database_service import DatabaseService
from app.extensions import Base  # Import the actual Base
from app.models import User  # Import a representative model
from app.config.settings import AppSettings
from logging import getLogger


@pytest.fixture(scope="module")
def in_memory_db():
    """
    Fixture to set up an in-memory SQLite database for the test module.
    - Creates an engine and a session factory.
    - Creates all tables defined in the application's models.
    - Yields the session factory to the tests.
    - Tears down all tables after the tests are complete.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(in_memory_db):
    """
    Fixture to provide a clean database session for each test function.
    - Creates a new session from the in-memory DB factory.
    - Ensures the session is closed after the test runs.
    """
    session = in_memory_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_settings() -> AppSettings:
    """Fixture to provide a mock AppSettings object."""
    return AppSettings(ENVIRONMENT="testing", DATABASE_URL="sqlite:///:memory:")


@pytest.fixture
def mock_logger():
    """Fixture to provide a mock logger."""
    return getLogger("test_logger")


@pytest.fixture
def database_service(db_session, mock_logger, mock_settings) -> DatabaseService:
    """Fixture to provide an instance of the DatabaseService."""
    return DatabaseService(session=db_session, logger=mock_logger, settings=mock_settings)


def test_database_service_health_check_healthy(database_service: DatabaseService):
    """
    GIVEN a DatabaseService instance connected to a healthy in-memory DB
    WHEN the get_database_health method is called
    THEN it should return a 'healthy' status.
    """
    # ACT
    health = database_service.get_database_health()

    # ASSERT
    assert health["status"] == "healthy"
    assert health["checks"]["connection"]["status"] == "ok"


def test_create_and_get_record(database_service: DatabaseService, db_session):
    """
    GIVEN a DatabaseService instance
    WHEN a new record is created and then retrieved
    THEN the retrieved record should match the created data.
    """
    # ARRANGE
    table_name = "users"
    user_data = {"full_name": "Test User", "email": "test@example.com", "is_admin": False}

    # Need to set password separately if the model requires it
    user = User(**user_data)
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()

    # ACT
    retrieved_record = database_service.get_record(table_name, user.id)

    # ASSERT
    assert retrieved_record["status"] == "success"
    assert retrieved_record["data"]["full_name"] == user_data["full_name"]
    assert retrieved_record["data"]["email"] == user_data["email"]


def test_get_record_not_found(database_service: DatabaseService):
    """
    GIVEN a DatabaseService instance
    WHEN a non-existent record is requested
    THEN it should return a 'not found' error.
    """
    # ACT
    result = database_service.get_record("users", 99999)

    # ASSERT
    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


def test_update_record(database_service: DatabaseService, db_session):
    """
    GIVEN an existing record
    WHEN the record is updated via the DatabaseService
    THEN the changes should be persisted in the database.
    """
    # ARRANGE
    user = User(full_name="Original Name", email="update@example.com")
    user.set_password("password")
    db_session.add(user)
    db_session.commit()

    update_data = {"full_name": "Updated Name"}

    # ACT
    update_result = database_service.update_record("users", user.id, update_data)

    # Manually refresh the user object to see the changes
    db_session.refresh(user)

    # ASSERT
    assert update_result["status"] == "success"
    assert user.full_name == "Updated Name"


def test_delete_record(database_service: DatabaseService, db_session):
    """
    GIVEN an existing record
    WHEN the record is deleted via the DatabaseService
    THEN the record should no longer exist in the database.
    """
    # ARRANGE
    user = User(full_name="Delete Me", email="delete@example.com")
    user.set_password("password")
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # ACT
    delete_result = database_service.delete_record("users", user_id)

    # Manually check if the user still exists
    deleted_user = db_session.get(User, user_id)

    # ASSERT
    assert delete_result["status"] == "success"
    assert deleted_user is None


def test_execute_read_only_query(database_service: DatabaseService):
    """
    GIVEN a DatabaseService instance
    WHEN a read-only SELECT query is executed
    THEN it should return the correct results.
    """
    # ACT
    result = database_service.execute_query("SELECT 1 AS my_number")

    # ASSERT
    assert result["status"] == "success"
    assert result["columns"] == ["my_number"]
    assert result["rows"] == [{"my_number": 1}]


def test_execute_write_query_is_blocked(database_service: DatabaseService):
    """
    GIVEN a DatabaseService instance
    WHEN a write query (INSERT, UPDATE, DELETE) is executed
    THEN it should be blocked and return an error.
    """
    # ACT
    result = database_service.execute_query("INSERT INTO users (full_name) VALUES ('bad actor')")

    # ASSERT
    assert result["status"] == "error"
    assert "only select queries are allowed" in result["message"].lower()
