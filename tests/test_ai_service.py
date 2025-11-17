# tests/test_ai_service.py
"""
Unit Tests for the Standalone FastAPI AI Service
=================================================
Version: 2.0.0

This test suite validates the functionality of the standalone AI service,
ensuring it correctly handles streaming chat requests, authentication,
and error conditions.
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

# Ensure the app is imported correctly
from ai_service_standalone.main import ALGORITHM, SECRET_KEY, app

client = TestClient(app)


def create_test_token(user_id: str, secret: str, expires_in_minutes: int = 15) -> str:
    """Helper function to create a JWT for testing."""
    payload = {
        "exp": datetime.now(UTC) + timedelta(minutes=expires_in_minutes),
        "iat": datetime.now(UTC),
        "sub": user_id,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


# --- Test Cases ---


def test_stream_chat_success():
    """
    Tests a successful streaming chat request with a valid token and payload.
    """
    token = create_test_token("test_user_123", SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": "What is the meaning of life?", "conversation_id": "conv_abc"}

    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]

    # Process the streaming response
    lines = response.text.strip().split("\n")
    chunks = [json.loads(line) for line in lines if line]

    assert len(chunks) > 1, "Expected multiple chunks in the stream"

    # Verify the content of the chunks
    assert chunks[0]["type"] == "data"
    assert "content" in chunks[0]["payload"]
    reconstructed_message = "".join(c["payload"]["content"] for c in chunks if c["type"] == "data")
    assert "meaning of life" in reconstructed_message

    # Verify the end-of-stream message
    end_chunk = chunks[-1]
    assert end_chunk["type"] == "end"
    assert "conversation_id" in end_chunk["payload"]
    assert end_chunk["payload"]["conversation_id"] is not None


def test_stream_chat_no_auth_header():
    """
    Tests the endpoint's response when the Authorization header is missing.
    """
    payload = {"question": "This should fail."}
    response = client.post("/api/v1/chat/stream", json=payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "Authorization header missing"}


def test_stream_chat_invalid_token():
    """
    Tests the endpoint's response with an invalid or malformed JWT.
    """
    headers = {"Authorization": "Bearer an-invalid-token"}
    payload = {"question": "This should also fail."}
    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_stream_chat_expired_token():
    """
    Tests the endpoint's response with an expired JWT.
    """
    expired_token = create_test_token("test_user_456", SECRET_KEY, expires_in_minutes=-5)
    headers = {"Authorization": f"Bearer {expired_token}"}
    payload = {"question": "Testing with an expired token."}
    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        ({}, "Field required"),  # Missing 'question'
        ({"question": "   "}, "String should have at least 1 character"),  # Empty question
        (
            {"question": "Valid", "conversation_id": 123},
            "Input should be a valid string",
        ),  # Invalid conv_id type
    ],
)
def test_stream_chat_invalid_payload(payload, expected_error):
    """
    Tests the endpoint's response to various invalid payloads.
    """
    token = create_test_token("test_user_789", SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)
    assert response.status_code == 422  # Unprocessable Entity
    assert expected_error in response.text


@patch("ai_service_standalone.main.stream_ai_response")
def test_stream_chat_internal_ai_error(mock_stream_ai):
    """
    Tests how the endpoint handles an unexpected error from the AI service logic.
    """
    # Configure the mock to raise an exception
    mock_stream_ai.side_effect = Exception("A critical AI error occurred!")

    token = create_test_token("test_user_error", SECRET_KEY)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": "This will trigger an error."}

    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)

    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    lines = response.text.strip().split("\n")
    chunks = [json.loads(line) for line in lines if line]
    assert len(chunks) == 1
    error_chunk = chunks[0]
    assert error_chunk["type"] == "error"
    assert "An internal AI error occurred" in error_chunk["payload"]["error"]
