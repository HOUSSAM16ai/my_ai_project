from unittest.mock import MagicMock

import pytest

from app.services.fastapi_generation_service import get_generation_service


@pytest.fixture
def service():
    return get_generation_service()


@pytest.fixture
def mock_llm_client(monkeypatch):
    """
    Patches app.services.fastapi_generation_service.get_llm_client to return a mock.
    Uses monkeypatch instead of mocker (pytest-mock) to avoid dependency issues.
    """
    mock = MagicMock()
    monkeypatch.setattr("app.services.fastapi_generation_service.get_llm_client", lambda: mock)

    # Configure the mock chain for chat.completions.create
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mock response"))]
    mock.chat.completions.create.return_value = mock_response

    return mock


def test_forge_new_code(service, mock_llm_client):
    result = service.forge_new_code("test prompt")
    assert result["status"] == "success"
    assert result["answer"] == "Mock response"
    assert "meta" in result


def test_generate_json(service, mock_llm_client):
    # Update the content for this specific test
    mock_llm_client.chat.completions.create.return_value.choices[
        0
    ].message.content = '{"key": "value"}'

    result = service.generate_json("test json")

    assert result["status"] == "success"
    # Flexible assertion to handle potential formatting variations
    assert "key" in result["answer"] or "key" in str(result["answer"])


def test_diagnostics(service):
    diag = service.diagnostics()
    assert "version" in diag
    assert "selected_default_model" in diag


def test_execute_task_delegation(service, monkeypatch):
    """
    Verify that execute_task correctly delegates to TaskExecutor.
    Uses monkeypatch instead of mocker.
    """
    # Create the mock for TaskExecutor class
    mock_executor_class = MagicMock()
    mock_executor_instance = mock_executor_class.return_value

    # Patch the class in the module where it is imported/used
    # Note: execute_task does a local import: from app.services.task_executor_refactored import TaskExecutor
    # So we need to patch app.services.task_executor_refactored.TaskExecutor
    monkeypatch.setattr("app.services.task_executor_refactored.TaskExecutor", mock_executor_class)

    # Create a dummy task
    dummy_task = MagicMock()

    # Call the method
    service.execute_task(dummy_task, model="gpt-4")

    # Verify instantiation and execution
    mock_executor_class.assert_called_once_with(service)
    mock_executor_instance.execute.assert_called_once_with(dummy_task, "gpt-4")
