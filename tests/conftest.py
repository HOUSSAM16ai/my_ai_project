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
def session(app, db):
    """
    Creates a new database session for a test.
    
    CRITICAL FIX for Problem #1 (Inconsistent DB State):
    - Ensures test and Flask app share the same database session
    - Uses nested transactions for proper isolation
    - Maintains app context throughout the test
    """
    with app.app_context():
        # Start a connection
        connection = db.engine.connect()
        transaction = connection.begin()

        # Override the default session with one bound to our connection
        # This is the KEY to ensuring both test code and app code see the same data
        options = dict(bind=connection, binds={})
        session_factory = sessionmaker(**options)
        test_session = scoped_session(session_factory)
        
        # Replace db.session with our test session
        # This ensures all queries in the app and tests use the same session
        old_session = db.session
        db.session = test_session

        yield test_session

        # Cleanup: rollback transaction and restore original session
        test_session.remove()
        transaction.rollback()
        connection.close()
        db.session = old_session


@pytest.fixture(scope='function')
def client(app, session):
    """
    A test client for the app.
    
    CRITICAL FIX for Problem #2 (Authentication Persistence):
    - Depends on session fixture to ensure shared database state
    - Returns client directly without context manager to avoid nesting
    - App context is maintained by the session fixture
    """
    return app.test_client()

@pytest.fixture(scope='function')
def admin_user(app, session):
    """
    Create an admin user for testing.
    
    FIX for Problem #1 & #2:
    - Creates admin user in the shared session
    - Ensures user persists for authentication tests
    """
    user = User(
        email='admin@test.com',
        full_name='Admin User',
        is_admin=True
    )
    user.set_password('1111')
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope='function')
def init_database(app, db, session):
    """
    Initialize database with basic data.
    
    FIX for Problem #2:
    - Ensures database is ready for authentication tests
    - Creates tables if needed
    - Provides clean state for each test
    """
    # Tables are already created by the db fixture
    # This fixture just ensures they're ready
    yield db
    # Cleanup happens in session fixture


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
    """
    Factory to create a user.
    
    FIX for Problem #1:
    - Uses the shared session
    - Commits to ensure data is visible to both test and app code
    """
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
        session.commit()  # Commit to make visible to app code
        return user
    return _user_factory

@pytest.fixture
def mission_factory(session, user_factory):
    """
    Factory to create a mission.
    
    FIX for Problem #1:
    - Uses the shared session
    - Commits to ensure data is visible
    """
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
        session.commit()  # Commit to make visible to app code
        return mission
    return _mission_factory
