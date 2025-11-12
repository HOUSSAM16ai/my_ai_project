import os
from unittest.mock import MagicMock, patch

import openai
from fastapi.testclient import TestClient

from ai_service.main import app, get_ai_client, get_db

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "AI Oracle Online"}


def test_chat_completion():
    # Create a mock AI client
    mock_ai_client = MagicMock(spec=openai.OpenAI)
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Test response"
    mock_ai_client.chat.completions.create.return_value = mock_completion

    # Create an override function for the dependency
    def override_get_ai_client():
        return mock_ai_client

    # Apply the override
    app.dependency_overrides[get_ai_client] = override_get_ai_client

    # Make the request
    response = client.post("/ai/chat/completion", json={"model": "test-model", "messages": []})

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": "Test response"}


def test_generate_code_with_context():
    # Create a mock AI client
    mock_ai_client = MagicMock(spec=openai.OpenAI)
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "def new_function():\n    pass"
    mock_ai_client.chat.completions.create.return_value = mock_completion

    # Create an override function for the dependency
    def override_get_ai_client():
        return mock_ai_client

    # Apply the override
    app.dependency_overrides[get_ai_client] = override_get_ai_client

    # Make the request
    payload = {"prompt": "Create a new function", "context": "Existing code"}
    response = client.post("/ai/generate/code", json=payload)

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "success", "generated_code": "def new_function():\n    pass"}


def test_test_ai_connection():
    # Create a mock AI client
    mock_ai_client = MagicMock(spec=openai.OpenAI)
    mock_models = MagicMock()
    mock_models.data = [1, 2, 3]
    mock_ai_client.models.list.return_value = mock_models

    # Create an override function for the dependency
    def override_get_ai_client():
        return mock_ai_client

    # Apply the override
    app.dependency_overrides[get_ai_client] = override_get_ai_client

    # Make the request
    response = client.get("/diagnostics/ai-connection")

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Successfully connected. 3 models available."}


def test_get_user_count():
    # Create a mock DB session
    mock_db_session = MagicMock()
    mock_db_session.execute.return_value.scalar_one.return_value = 10

    # Create an override function for the dependency
    def override_get_db():
        yield mock_db_session

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # Make the request
    response = client.get("/admin/vitals/user-count")

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": 10}


def test_list_all_users():
    # Create a mock DB session
    mock_db_session = MagicMock()
    mock_users = [
        {"id": 1, "full_name": "User 1", "email": "user1@example.com"},
        {"id": 2, "full_name": "User 2", "email": "user2@example.com"},
    ]
    mock_db_session.execute.return_value.mappings.return_value.all.return_value = mock_users

    # Create an override function for the dependency
    def override_get_db():
        yield mock_db_session

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # Make the request
    response = client.get("/admin/vitals/users")

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": mock_users}


def test_chat_completion_api_error():
    # Create a mock AI client that raises an exception
    mock_ai_client = MagicMock(spec=openai.OpenAI)
    mock_ai_client.chat.completions.create.side_effect = Exception("API Error")

    # Create an override function for the dependency
    def override_get_ai_client():
        return mock_ai_client

    # Apply the override
    app.dependency_overrides[get_ai_client] = override_get_ai_client

    # Make the request
    response = client.post("/ai/chat/completion", json={"model": "test-model", "messages": []})

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 500
    assert response.json() == {"detail": "API Error"}


def test_get_user_count_db_error():
    # Create a mock DB session that raises an exception
    mock_db_session = MagicMock()
    mock_db_session.execute.side_effect = Exception("DB query failed")

    # Create an override function for the dependency
    def override_get_db():
        yield mock_db_session

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # Make the request
    response = client.get("/admin/vitals/user-count")

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 500
    assert response.json() == {"detail": "Database query failed: DB query failed"}


def test_list_all_users_db_error():
    # Create a mock DB session that raises an exception
    mock_db_session = MagicMock()
    mock_db_session.execute.side_effect = Exception("DB query failed")

    # Create an override function for the dependency
    def override_get_db():
        yield mock_db_session

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # Make the request
    response = client.get("/admin/vitals/users")

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 500
    assert response.json() == {"detail": "Database query failed: DB query failed"}


def test_generate_code_with_context_api_error():
    # Create a mock AI client that raises an exception
    mock_ai_client = MagicMock(spec=openai.OpenAI)
    mock_ai_client.chat.completions.create.side_effect = Exception("API Error")

    # Create an override function for the dependency
    def override_get_ai_client():
        return mock_ai_client

    # Apply the override
    app.dependency_overrides[get_ai_client] = override_get_ai_client

    # Make the request
    payload = {"prompt": "Create a new function", "context": "Existing code"}
    response = client.post("/ai/generate/code", json=payload)

    # Clean up the override
    app.dependency_overrides.clear()

    # Assert the response
    assert response.status_code == 500
    assert response.json() == {"detail": "API Error"}


@patch("ai_service.main.create_engine", side_effect=Exception("DB connection failed"))
def test_lifespan_db_connection_failure(mock_create_engine):
    with TestClient(app) as client:
        # The lifespan event should run on startup. We don't need to make a request.
        # We can check the app state to see if the session factory is None.
        assert app.state.db_session_factory is None


@patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True)
def test_lifespan_no_api_key():
    with TestClient(app) as client:
        assert app.state.ai_client is None
