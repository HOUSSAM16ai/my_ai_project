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
from unittest.mock import MagicMock, patch

import pytest
import requests


@pytest.fixture
def mock_failing_gateway():
    """Mocks an AI gateway that simulates a connection error."""
    mock_gateway = MagicMock()
    mock_gateway.stream_chat.side_effect = requests.exceptions.ConnectionError(
        "Failed to connect to AI service"
    )
    return mock_gateway


def test_chat_stream_gateway_connection_error(
    admin_user, client, mock_failing_gateway, admin_auth_headers
):
    """
    Tests how the endpoint handles a connection error from the AI service gateway.
    It should return a user-friendly error message within the SSE stream.
    """
    with patch(
        "app.services.ai_service_gateway.get_ai_service_gateway",
        return_value=mock_failing_gateway,
    ):
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
    The endpoint should return a user-friendly error message within the SSE stream.
    """
    # Patch the factory function to return None
    with patch("app.services.ai_service_gateway.get_ai_service_gateway", return_value=None):
        response = client.post(
            "/admin/api/chat/stream", json={"question": "Test question"}, headers=admin_auth_headers
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    lines = [line for line in response.text.strip().split("\n") if line]
    last_line = lines[-1] if lines else ""
    assert last_line.startswith("data: ")

    chunk = json.loads(last_line[6:])
    assert chunk["type"] == "error"
    assert "AI service is currently unavailable" in chunk["payload"]["error"]


def test_chat_stream_missing_question_payload(admin_user, client, admin_auth_headers):
    """
    Tests that making a POST request with an empty or missing 'question'
    results in a user-friendly error message within the SSE stream.
    """
    # Test with empty JSON payload
    response = client.post("/admin/api/chat/stream", json={}, headers=admin_auth_headers)
    assert response.status_code == 200
    lines = [line for line in response.text.strip().split("\n") if line]
    last_line = lines[-1] if lines else ""
    assert last_line.startswith("data: ")
    chunk = json.loads(last_line[6:])
    assert chunk["type"] == "error"
    assert "Question is required" in chunk["payload"]["error"]

    # Test with question being an empty string
    response = client.post(
        "/admin/api/chat/stream", json={"question": "  "}, headers=admin_auth_headers
    )
    assert response.status_code == 200
    lines = [line for line in response.text.strip().split("\n") if line]
    last_line = lines[-1] if lines else ""
    assert last_line.startswith("data: ")
    chunk = json.loads(last_line[6:])
    assert chunk["type"] == "error"
    assert "Question is required" in chunk["payload"]["error"]
