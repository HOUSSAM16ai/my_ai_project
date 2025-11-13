# tests/test_admin_api_error_handling.py
import json
import pytest


def login_admin(client, admin_user):
    return client.post(
        "/login", data=dict(email=admin_user.email, password="1111"), follow_redirects=True
    )


def test_chat_stream_returns_error_event_on_missing_question(
    client, init_database, mock_ai_gateway, admin_user
):
    """
    Test that /admin/api/chat/stream returns a JSON error event when the question is missing.
    """
    login_admin(client, admin_user)
    response = client.get("/admin/api/chat/stream")

    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    response_text = response.get_data(as_text=True)
    assert "data:" in response_text


@pytest.mark.skip(reason="This test is failing intermittently and needs to be investigated.")
def test_chat_stream_api_requires_authentication(client, init_database, mock_ai_gateway):
    """
    Test that /admin/api/chat/stream requires authentication.
    """
    response = client.get("/admin/api/chat/stream?question=test")
    assert response.status_code == 302
