# tests/conftest.py
import pytest
from app import create_app, db as _db
from app.models import User, Mission
from unittest.mock import MagicMock, patch
from faker import Faker
import os

# Initialize Faker
fake = Faker()

os.environ['HF_HOME'] = '/tmp/huggingface'

@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance for the test session."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    return _db

@pytest.fixture(scope='function')
def session(app, db):
    """
    Creates a new database session for a test within a nested transaction.
    This ensures tests run in isolation and get rolled back after execution.
    Handles cases where the transaction might be closed by the app code.
    """
    with app.app_context():
        transaction = db.session.begin_nested()
        yield db.session
        if transaction.is_active:
            transaction.rollback()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app for each function."""
    return app.test_client()

@pytest.fixture
def mock_ai_gateway():
    """Mock the AI service gateway."""
    mock_gateway = MagicMock()
    def mock_stream_chat(question, conversation_id):
        responses = [
            {"type": "data", "payload": {"content": "This "}},
            {"type": "data", "payload": {"content": "is "}},
            {"type": "data", "payload": {"content": "a "}},
            {"type": "data", "payload": {"content": "mocked "}},
            {"type": "data", "payload": {"content": "response."}},
            {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}
        ]
        yield from responses
    mock_gateway.stream_chat.side_effect = mock_stream_chat
    with patch('app.admin.routes.get_ai_service_gateway', return_value=mock_gateway) as mock:
        yield mock

@pytest.fixture
def admin_user(session):
    """
    Create an admin user within the test transaction.
    Uses flush to make the user available in the DB for the test without committing.
    """
    user = User.query.filter_by(email="admin@test.com").first()
    if user is None:
        user = User(email="admin@test.com", full_name="Admin User", is_admin=True)
        user.set_password("password")
        session.add(user)
        session.flush()
    return user

# -----------------------------------------------------------------------------
# Factories
# -----------------------------------------------------------------------------
@pytest.fixture
def user_factory(session):
    """Factory to create a user. Uses flush."""
    def _user_factory(**kwargs):
        defaults = {
            'email': fake.email(),
            'full_name': fake.name(),
        }
        defaults.update(kwargs)
        password = defaults.pop('password', 'password')
        user = User(**defaults)
        user.set_password(password)
        session.add(user)
        session.flush()
        return user
    return _user_factory

@pytest.fixture
def mission_factory(session, user_factory):
    """Factory to create a mission. Uses flush."""
    def _mission_factory(**kwargs):
        if 'initiator' not in kwargs and 'initiator_id' not in kwargs:
            kwargs['initiator'] = user_factory()
        defaults = {
            'objective': fake.sentence(),
            'status': 'PENDING',
        }
        defaults.update(kwargs)
        mission = Mission(**defaults)
        session.add(mission)
        session.flush()
        return mission
    return _mission_factory
