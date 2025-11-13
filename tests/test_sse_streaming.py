# tests/test_sse_streaming.py
import json
import pytest


def login_admin(client):
    return client.post(
        "/login", data=dict(email="admin@test.com", password="password"), follow_redirects=True
    )


def test_admin_chat_stream_requires_auth(client, session, mock_ai_gateway):
    response = client.get("/admin/api/chat/stream?question=test")
    # Non-logged in users are redirected to login page by default from Flask-Login
    assert response.status_code == 302


def test_admin_chat_stream_sse_format(client, session, mock_ai_gateway):
    login_admin(client)
    response = client.get("/admin/api/chat/stream?question=hello")
    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    # A simple check for SSE data format
    response_text = response.get_data(as_text=True)
    assert "data:" in response_text
