# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User
from unittest.mock import MagicMock, patch

@pytest.fixture(scope='session')
def app():
    """Create a Flask app instance for the test session."""
    return create_app('testing')

@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='module')
def init_database(app):
    """Create the database."""
    with app.app_context():
        db.create_all()
        admin_user = User(email="admin@test.com", full_name="Admin User", is_admin=True)
        admin_user.set_password("password")
        db.session.add(admin_user)
        db.session.commit()
        yield db
        db.drop_all()

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
