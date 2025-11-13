# tests/test_sse_streaming.py
import json
import pytest


def login_admin(client, admin_user):
    """Helper to login as admin user"""
    return client.post(
        "/login",
        data=dict(email=admin_user.email, password="1111"),  # Match admin_user fixture password
        follow_redirects=True,
    )


def test_admin_chat_stream_requires_auth(client, init_database):
    response = client.get("/admin/api/chat/stream?question=test")
    # Non-logged in users are redirected to login page by default from Flask-Login
    assert response.status_code == 302


def test_admin_chat_stream_sse_format(client, init_database, admin_user, mock_ai_gateway):
    # Login with the admin user
    login_response = login_admin(client, admin_user)
    assert login_response.status_code == 200

    # Now make the actual request
    response = client.get("/admin/api/chat/stream?question=hello")
    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    # A simple check for SSE data format
    response_text = response.get_data(as_text=True)
    assert "data:" in response_text
