# tests/test_admin_chat_complex_questions.py
import pytest
import json

def test_chat_stream_handles_complex_arabic_question(admin_user, client, mock_ai_gateway, session):
    """
    Test that the streaming endpoint can handle a complex Arabic question.
    """
    # Log in
    client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)

    complex_question = "شرح بنية المشروع والملفات المختلفة واشرح لي كيف يعمل نظام قاعدة البيانات"

    response = client.post(
        "/admin/api/chat/stream",
        json={"question": complex_question}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.mimetype

    # Check that we received a valid stream with mocked data
    content = response.get_data(as_text=True)
    assert 'data: {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}' in content

def test_chat_stream_handles_very_long_question(admin_user, client, mock_ai_gateway, session):
    """
    Test that the streaming endpoint can handle a very long question.
    """
    # Log in
    client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)

    long_question = "شرح " + ("المشروع " * 1000) # Roughly 5000 chars

    response = client.post(
        "/admin/api/chat/stream",
        json={"question": long_question}
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.mimetype

    # Check for a valid stream end
    content = response.get_data(as_text=True)
    assert 'data: {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}' in content
