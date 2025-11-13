# tests/conftest.py - The Gold Standard Test Setup (vSuperhuman Final)
# This setup is robust, simple, and follows best practices for testing Flask apps.
# It ensures every test runs in a clean, isolated database transaction.

import pytest
from app import create_app, db as _db
from app.models import User, Mission
from unittest.mock import MagicMock, patch
from faker import Faker

# Initialize Faker
fake = Faker()

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    _app = create_app('testing')
    return _app

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    with app.app_context():
        _db.create_all()
        admin = User(email="admin@test.com", full_name="Admin User", is_admin=True)
        admin.set_password("password")
        _db.session.add(admin)
        _db.session.commit()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(app, db):
    """
    Rolls back the database transaction after each test.
    This is the classic, simplest, and most reliable way to isolate tests.
    """
    with app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app, created new for each test function."""
    return app.test_client()

@pytest.fixture
def mock_ai_gateway():
    """Mock the AI service gateway."""
    mock_gateway = MagicMock()
    def mock_stream_chat(question, conversation_id):
        yield 'data: {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}\n\n'
    mock_gateway.stream_chat.side_effect = mock_stream_chat
    with patch("app.admin.routes.get_ai_service_gateway", return_value=mock_gateway) as mock:
        yield mock

# --- Factories ---
@pytest.fixture
def user_factory(session):
    def _user_factory(**kwargs):
        password = kwargs.pop("password", "password")
        defaults = {"email": fake.email(), "full_name": fake.name()}
        defaults.update(kwargs)
        user = User(**defaults)
        user.set_password(password)
        session.add(user)
        session.flush()
        return user
    return _user_factory

@pytest.fixture
def mission_factory(session, user_factory):
    def _mission_factory(**kwargs):
        if "initiator" not in kwargs:
            kwargs["initiator"] = user_factory()
        defaults = {"objective": fake.sentence(), "status": "PENDING"}
        defaults.update(kwargs)
        mission = Mission(**defaults)
        session.add(mission)
        session.flush()
        return mission
    return _mission_factory
