from unittest.mock import MagicMock

import pytest

from app.services.fastapi_generation_service import get_generation_service


@pytest.fixture
def service():
    return get_generation_service()


@pytest.fixture
def mock_llm_client(monkeypatch):
    """
    Patches the LLM client at the infrastructure layer.
    """
    mock = MagicMock()
    
    # Patch at the infrastructure adapter level
    monkeypatch.setattr("app.services.llm_client_service.get_llm_client", lambda: mock)

    # Configure the mock chain for chat.completions.create
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mock response"))]
    mock.chat.completions.create.return_value = mock_response

    return mock


def test_forge_new_code(service, mock_llm_client):
    result = service.forge_new_code("test prompt")
    assert result["status"] == "success"
    assert "answer" in result
    assert "meta" in result


def test_generate_json(service, mock_llm_client):
    # Update the content for this specific test
    mock_llm_client.chat.completions.create.return_value.choices[
        0
    ].message.content = '{"key": "value"}'

    result = service.generate_json("test json")

    assert result["status"] == "success"
    assert "answer" in result


def test_diagnostics(service):
    diag = service.diagnostics()
    assert "version" in diag
    assert "selected_default_model" in diag


def test_execute_task_delegation(service):
    """
    Verify that execute_task raises NotImplementedError.
    
    Task execution has been moved to overmind/executor.py.
    This test verifies the adapter correctly indicates the feature is not available.
    """
    # Create a dummy task
    dummy_task = MagicMock()

    # Call the method and expect NotImplementedError
    with pytest.raises(NotImplementedError, match="Task execution has been moved"):
        service.execute_task(dummy_task, model="gpt-4")
