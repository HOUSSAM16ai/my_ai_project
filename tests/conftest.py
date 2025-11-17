# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from faker import Faker

# Correctly import the db object from the extensions module
from app.extensions import db as _db
from app.models import Mission, User


@pytest.fixture(scope="session")
def app():
    """Yields the FastAPI application instance for testing."""
    yield fastapi_app


@pytest.fixture(scope="module")
def client(app):
    """A test client for the app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db():
    """
    Session-wide test database.
    Handles schema creation and teardown.
    """
    # Import models to ensure they are registered with the Base metadata
    from app import models
    _db.metadata.create_all(bind=_db.engine)
    yield _db
    _db.metadata.drop_all(bind=_db.engine)


@pytest.fixture(scope="function")
def session(db):
    """
    Creates a new database session for a test with transaction isolation.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    db.session.begin_nested()

    yield db.session

    db.session.rollback()
    transaction.rollback()
    connection.close()
    db.session.remove()


@pytest.fixture(scope="function")
def admin_user(session):
    user = User(email="admin@test.com", full_name="Admin User", is_admin=True)
    user.set_password("1111")
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def user_factory(session):
    """A factory for creating users."""
    def _create_user(**kwargs):
        user = User(**kwargs)
        session.add(user)
        session.commit()
        return user
    return _create_user


@pytest.fixture
def mission_factory(session, admin_user):
    """A factory for creating missions."""
    def _create_mission(**kwargs):
        if "initiator_id" not in kwargs:
            kwargs["initiator_id"] = admin_user.id
        mission = Mission(**kwargs)
        session.add(mission)
        session.commit()
        return mission
    return _create_mission
