"""
Test for empty AI response handling fix.

This test verifies that the system properly handles cases where the AI
returns None or empty content, which was causing blank responses in the UI.
"""

from unittest.mock import Mock, patch

import pytest

from app.services.admin_ai_service import AdminAIService


@pytest.fixture
def ai_service():
    """Create an instance of AdminAIService"""
    return AdminAIService()


@pytest.fixture
def mock_user():
    """Create a mock user object"""
    user = Mock()
    user.id = 1
    user.name = "Test User"
    user.email = "test@example.com"
    return user


def _run_test_with_mock_response(ai_service, mock_user, mock_response, question):
    """Helper function to run a test with a mocked AI response."""
    with (
        patch("app.services.admin_ai_service.get_llm_client") as mock_get_client,
        patch("os.getenv") as mock_getenv,
    ):
        mock_getenv.return_value = "test-api-key"
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        return ai_service.answer_question(
            question=question, user=mock_user, conversation_id=None, use_deep_context=False
        )


def test_empty_response_handling_none_content(ai_service, mock_user):
    """
    Test that None content from AI is handled gracefully.
    """
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage.total_tokens = 1000
    mock_response.model = "anthropic/claude-3.7-sonnet:thinking"

    result = _run_test_with_mock_response(ai_service, mock_user, mock_response, "السلام عليكم")

    assert result is not None
    assert result["status"] == "error"
    assert "answer" in result
    assert result["answer"] is not None and len(result["answer"]) > 0
    assert "لم يُرجع أي محتوى" in result["answer"] or "did not return any content" in result["answer"]
    assert "tokens_used" in result
    assert result["model_used"] == "anthropic/claude-3.7-sonnet:thinking"


def test_empty_response_handling_empty_string(ai_service, mock_user):
    """
    Test that empty string content from AI is handled gracefully.
    """
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = ""
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage.total_tokens = 500
    mock_response.model = "openai/gpt-4o"

    result = _run_test_with_mock_response(ai_service, mock_user, mock_response, "لماذا لا تظهر الكتابة")

    assert result is not None
    assert result["status"] == "error"
    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "لم يُرجع أي محتوى" in result["answer"] or "did not return any content" in result["answer"]


def test_empty_response_with_tool_calls(ai_service, mock_user):
    """
    Test handling of responses with tool calls but no content.
    """
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = [{"type": "function", "name": "test"}]
    mock_response.usage.total_tokens = 300
    mock_response.model = "openai/gpt-4o"

    result = _run_test_with_mock_response(ai_service, mock_user, mock_response, "test question")

    assert result is not None
    assert result["status"] == "error"
    assert "answer" in result
    assert "tool" in result["answer"].lower() or "أدوات" in result["answer"]


def test_normal_response_still_works(ai_service, mock_user):
    """
    Test that normal responses with content still work correctly.
    """
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "مرحباً! كيف يمكنني مساعدتك؟"
    mock_response.usage.total_tokens = 200
    mock_response.model = "openai/gpt-4o"

    result = _run_test_with_mock_response(ai_service, mock_user, mock_response, "السلام عليكم")

    assert result is not None
    assert result["status"] == "success"
    assert "answer" in result
    assert result["answer"] == "مرحباً! كيف يمكنني مساعدتك؟"
    assert result["tokens_used"] == 200
