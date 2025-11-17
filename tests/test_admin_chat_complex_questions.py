# tests/test_admin_chat_complex_questions.py
"""
Tests for Handling Complex and Long Questions in Admin Chat
============================================================
Version: 2.0.0

This test suite ensures the admin chat stream can handle complex, long, and
potentially problematic questions gracefully by using the POST method.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_ai_gateway():
    """Mocks the AI gateway to simulate a detailed response for complex questions."""
    mock_gateway = MagicMock()

    async def mock_stream_chat(question):
        """Simulated stream that echoes parts of the complex question."""
        if "database system" in question:
            yield {"type": "data", "payload": {"content": "Acknowledged database query. "}}
        elif "project structure" in question:
            yield {"type": "data", "payload": {"content": "Analyzing project structure."}}
        else:
            yield {"type": "data", "payload": {"content": "Understood long question. "}}

        yield {"type": "end", "payload": {"conversation_id": "conv_complex"}}

    mock_gateway.stream_chat = mock_stream_chat
    return mock_gateway


def test_chat_stream_handles_complex_question_via_post(
    admin_user, client, mock_ai_gateway, admin_auth_headers
):
    """
    Tests that a complex, multi-part question is handled correctly via a POST request.
    """
    complex_question = "Please explain the project structure, the different files, and how the database system works."

    with patch(
        "app.services.ai_service_gateway.get_ai_service_gateway", return_value=mock_ai_gateway
    ):
        response = client.post(
            "/admin/api/chat/stream",
            json={"question": complex_question},
            headers=admin_auth_headers,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    lines = [line for line in response.text.strip().split("\n") if line]
    assert len(lines) > 0


def test_chat_stream_handles_long_question_via_post(
    admin_user, client, mock_ai_gateway, admin_auth_headers
):
    """
    Tests that a very long question is handled correctly without errors via a POST request.
    """
    # Create a long question that might cause issues in a GET request URL
    long_question = ("Explain " + ("the project " * 500)).strip()

    with patch(
        "app.services.ai_service_gateway.get_ai_service_gateway", return_value=mock_ai_gateway
    ):
        response = client.post(
            "/admin/api/chat/stream",
            json={"question": long_question},
            headers=admin_auth_headers,
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    lines = [line for line in response.text.strip().split("\n") if line]
    assert len(lines) > 0
