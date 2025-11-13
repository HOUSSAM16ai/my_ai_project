# tests/conftest.py
import pytest
from app import create_app, db as _db
from app.models import User, Mission
from unittest.mock import MagicMock, patch
from faker import Faker
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import Connection

# Initialize Faker
fake = Faker()

@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance for the test session."""
    return create_app('testing')

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    with app.app_context():
        _db.app = app
        _db.create_all()

    yield _db

    with app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """
    Creates a new database session for a test.
    - Uses SAVEPOINTs for nested transactions.
    - Rolls back to the SAVEPOINT after the test.
    - Closes the connection to release it back to the pool.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    # Use scoped_session to ensure the session is managed properly
    options = dict(bind=connection, binds={})
    session = scoped_session(sessionmaker(**options))

    # The session is now bound to the connection, and the transaction has begun.
    db.session = session

    yield session

    # Rollback the transaction and close the connection
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
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

# -----------------------------------------------------------------------------
# Factories
# -----------------------------------------------------------------------------
@pytest.fixture
def user_factory(session):
    """Factory to create a user."""
    def _user_factory(**kwargs):
        defaults = {
            'email': fake.email(),
            'full_name': fake.name(),
        }
        defaults.update(kwargs)

        user = User(**defaults)
        if 'password' in defaults:
            user.set_password(defaults['password'])
        else:
            user.set_password('password')

        session.add(user)
        # We don't commit here; let the test decide when to commit.
        return user
    return _user_factory

@pytest.fixture
def mission_factory(session, user_factory):
    """Factory to create a mission."""
    def _mission_factory(**kwargs):
        # Ensure there's an initiator for the mission
        if 'initiator' not in kwargs and 'initiator_id' not in kwargs:
            kwargs['initiator'] = user_factory()

        defaults = {
            'objective': fake.sentence(),
            'status': 'PENDING',
        }
        defaults.update(kwargs)

        mission = Mission(**defaults)
        session.add(mission)
        return mission
    return _mission_factory
