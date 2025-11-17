# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """
    A test client for the app.
    """
    with TestClient(app) as c:
        yield c


# The following fixtures are commented out as they are based on the old Flask
# application structure. They will need to be refactored to work with the
# new FastAPI architecture and its dependency injection system.

# from unittest.mock import MagicMock, patch
# from faker import Faker
# from sqlalchemy.orm import scoped_session, sessionmaker
# from app.models import Mission, User
# from app import db as _db

# fake = Faker()

# @pytest.fixture(scope="session")
# def db(app):
#     """Session-wide test database."""
#     with app.app_context():
#         _db.app = app
#         _db.create_all()
#     yield _db
#     with app.app_context():
#         _db.drop_all()

# @pytest.fixture(scope="function")
# def session(app, db):
#     with app.app_context():
#         connection = db.engine.connect()
#         transaction = connection.begin()
#         options = dict(bind=connection, binds={})
#         session_factory = sessionmaker(**options)
#         test_session = scoped_session(session_factory)
#         old_session = db.session
#         db.session = test_session
#         yield test_session
#         test_session.remove()
#         transaction.rollback()
#         connection.close()
#         db.session = old_session

# @pytest.fixture(scope="function")
# def admin_user(app, session):
#     user = User(email="admin@test.com", full_name="Admin User", is_admin=True)
#     user.set_password("1111")
#     session.add(user)
#     session.commit()
#     return user

# @pytest.fixture
# def mock_ai_gateway():
#     """Mock the AI service gateway."""
#     mock_gateway = MagicMock()
#     def mock_stream_chat(question, conversation_id, user_id):
#         responses = [
#             {"type": "data", "payload": {"content": "This "}},
#             {"type": "data", "payload": {"content": "is "}},
#             {"type": "data", "payload": {"content": "a "}},
#             {"type": "data", "payload": {"content": "mocked "}},
#             {"type": "data", "payload": {"content": "response."}},
#             {"type": "end", "payload": {"conversation_id": "mock_conv_123"}},
#         ]
#         yield from responses
#     mock_gateway.stream_chat.side_effect = mock_stream_chat
#     with patch("app.admin.routes.get_ai_service_gateway", return_value=mock_gateway) as mock:
#         yield mock
