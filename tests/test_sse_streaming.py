# tests/test_sse_streaming.py
import pytest
import json

def test_admin_chat_stream_requires_auth(client):
    """Test that the admin chat stream endpoint requires authentication."""
    response = client.post("/admin/api/chat/stream", json={"question": "test"})
    assert response.status_code in [302, 401]

def test_admin_chat_stream_success(admin_user, client, mock_ai_gateway, session):
    """Test a successful chat stream call."""
    with client:
        client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)
        response = client.post(
            "/admin/api/chat/stream",
            json={"question": "Hello", "conversation_id": "test_conv_123"}
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.mimetype

    content = response.get_data(as_text=True)
    assert 'data: {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}' in content

def test_admin_chat_stream_no_question(admin_user, client, session):
    """Test the stream response when no question is provided."""
    with client:
        client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)
        response = client.post("/admin/api/chat/stream", json={})

    assert response.status_code == 200
    assert "text/event-stream" in response.mimetype

    content = response.get_data(as_text=True)
    assert 'data: {"type": "error", "payload": {"error_message": "Question is required"}}' in content
