# tests/test_admin_chat_complex_questions.py
import json
import pytest


def login_admin(client):
    return client.post(
        "/login", data=dict(email="admin@test.com", password="password"), follow_redirects=True
    )


def test_chat_stream_handles_complex_question(client, session, mock_ai_gateway):
    login_admin(client)
    complex_question = "شرح بنية المشروع والملفات المختلفة واشرح لي كيف يعمل نظام قاعدة البيانات"
    response = client.get(f"/admin/api/chat/stream?question={complex_question}")

    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    response_text = response.get_data(as_text=True)
    assert "data:" in response_text


def test_chat_stream_handles_long_question(client, session, mock_ai_gateway):
    login_admin(client)
    long_question = "شرح " + ("المشروع " * 200)  # Roughly 1400 chars, well within limits
    response = client.get(f"/admin/api/chat/stream?question={long_question}")

    assert response.status_code == 200
    assert "text/event-stream" in response.content_type

    response_text = response.get_data(as_text=True)
    assert "data:" in response_text
