# tests/test_admin_api_error_handling.py
import pytest
import json

def test_chat_stream_api_requires_authentication(client):
    """
    Test that the /admin/api/chat/stream endpoint requires authentication.
    """
    response = client.post(
        "/admin/api/chat/stream",
        json={"question": "test"}
    )
    # Expect redirect to login page (302) or an unauthorized error (401)
    assert response.status_code in [302, 401]

def test_chat_stream_api_returns_json_error_on_invalid_json(admin_user, client, session):
    """
    Test that /admin/api/chat/stream returns a proper error for invalid JSON.
    Note: Flask's behavior for invalid JSON might result in a generic bad request response.
    This test verifies that the application handles it gracefully.
    """
    # Log in
    client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)

    response = client.post(
        "/admin/api/chat/stream",
        data="not a valid json",
        content_type="application/json"
    )

    # Expect a Bad Request error
    assert response.status_code == 400

def test_chat_stream_api_handles_missing_question(admin_user, client, session):
    """
    Test that the streaming API sends a specific SSE error event if 'question' is missing.
    """
    # Log in
    client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)

    response = client.post(
        "/admin/api/chat/stream",
        json={"conversation_id": "some_id"}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.mimetype

    content = response.get_data(as_text=True)
    assert 'data: {"type": "error", "payload": {"error_message": "Question is required"}}' in content
