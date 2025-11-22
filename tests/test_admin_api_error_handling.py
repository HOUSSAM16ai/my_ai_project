# tests/test_admin_api_error_handling.py
"""
Tests for API Error Handling in the Admin Chat Endpoint
========================================================
Version: 2.0.0

This test suite focuses on ensuring the /admin/api/chat/stream endpoint
handles various error conditions gracefully, providing clear and correct
feedback to the client.
"""

import json
from unittest.mock import MagicMock

import pytest
import requests
from app.main import kernel
from app.core.ai_gateway import get_ai_client

def test_chat_stream_gateway_connection_error(
    admin_user, client, admin_auth_headers, mock_ai_client_global
):
    """
    Tests how the endpoint handles a connection error from the AI service gateway.
    It should return a user-friendly error message within the SSE stream.
    """
    # Configure the global mock to fail
    # Since mock_ai_client_global.stream_chat is an async generator function, we replace it.
    async def failing_stream(messages):
        # Yield nothing, just raise
        if False: yield # make it a generator
        raise requests.exceptions.ConnectionError("Failed to connect to AI service")

    mock_ai_client_global.stream_chat = failing_stream

    response = client.post(
        "/admin/api/chat/stream",
        json={"question": "This will cause a connection error."},
        headers=admin_auth_headers,
    )

    # The overall request is successful (200), but the stream contains an error
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    # The stream should contain the error message in the last non-empty chunk
    lines = [line for line in response.text.strip().split("\n") if line]
    last_line = lines[-1] if lines else ""
    assert last_line.startswith("data: ")

    chunk = json.loads(last_line[6:])

    assert chunk["type"] == "error"
    assert "payload" in chunk
    assert "error" in chunk["payload"]
    assert "Failed to connect to AI service" in chunk["payload"]["error"]


def test_chat_stream_gateway_not_configured(admin_user, client, admin_auth_headers):
    """
    Tests the scenario where the AI gateway is not configured or fails to initialize.
    The TestClient raises the exception because raise_server_exceptions is True by default.
    """
    # Override the dependency just for this test to simulate startup failure/factory failure
    def mock_get_client_error():
        raise ValueError("OPENROUTER_API_KEY is not set.")

    kernel.app.dependency_overrides[get_ai_client] = mock_get_client_error

    try:
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is not set"):
            client.post(
                "/admin/api/chat/stream", json={"question": "Test question"}, headers=admin_auth_headers
            )
    finally:
         if get_ai_client in kernel.app.dependency_overrides:
            del kernel.app.dependency_overrides[get_ai_client]


def test_chat_stream_missing_question_payload(admin_user, client, admin_auth_headers, mock_ai_client_global):
    """
    Tests that making a POST request with an empty or missing 'question'
    results in a user-friendly error message.
    """
    # Test with empty JSON payload (Pydantic validation error)
    response = client.post("/admin/api/chat/stream", json={}, headers=admin_auth_headers)
    assert response.status_code == 422
    # Validation error response format check
    assert response.json()["message"] == "Validation Error"

    # Test with question being an empty string (Custom logic check)
    response = client.post(
        "/admin/api/chat/stream", json={"question": "  "}, headers=admin_auth_headers
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Question is required."
