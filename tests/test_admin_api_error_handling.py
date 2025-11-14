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
    admin_user, test_client_with_user, mock_failing_gateway
):
    """
    Tests how the endpoint handles a connection error from the AI service gateway.
    It should return a user-friendly error message within the SSE stream.
    """
    with patch("app.admin.routes.get_ai_service_gateway", return_value=mock_failing_gateway):
        response = test_client_with_user.post(
            "/admin/api/chat/stream",
            json={"question": "This will cause a connection error."}
        )

    # The overall request is successful (200), but the stream contains an error
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    # The stream should contain a single event: the error message
    lines = response.data.decode("utf-8").strip().split("\n")
    assert len(lines) == 1
    assert lines[0].startswith("data: ")

    chunk = json.loads(lines[0][6:])

    assert chunk["type"] == "error"
    assert "payload" in chunk
    assert "error" in chunk["payload"]
    assert "Could not connect to the AI service" in chunk["payload"]["error"]


def test_chat_stream_gateway_not_configured(admin_user, test_client_with_user):
    """
    Tests the scenario where the AI gateway is not configured or fails to initialize.
    The endpoint should return a 503 Service Unavailable error.
    """
    # Patch the factory function to return None
    with patch("app.admin.routes.get_ai_service_gateway", return_value=None):
        response = test_client_with_user.post(
            "/admin/api/chat/stream",
            json={"question": "Test question"}
        )

    assert response.status_code == 503
    assert response.is_json
    json_response = response.get_json()
    assert json_response["status"] == "error"
    assert json_response["message"] == "AI service is currently unavailable."


def test_chat_stream_missing_question_payload(admin_user, test_client_with_user):
    """
    Tests that making a POST request with an empty or missing 'question'
    results in a 400 Bad Request error.
    """
    # Test with empty JSON payload
    response = test_client_with_user.post("/admin/api/chat/stream", json={})
    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["message"] == "Question is required."

    # Test with question being an empty string
    response = test_client_with_user.post("/admin/api/chat/stream", json={"question": "  "})
    assert response.status_code == 400
    assert response.get_json()["message"] == "Question is required."


def test_unauthenticated_access_is_redirected(test_client):
    """
    Confirms that an unauthenticated user is redirected to the login page.
    """
    response = test_client.post("/admin/api/chat/stream", json={"question": "test"})
    assert response.status_code == 302
    assert "login" in response.headers.get("Location", "")
