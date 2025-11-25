# tests/test_admin_chat_complex_questions.py
"""
Tests for Handling Complex and Long Questions in Admin Chat
============================================================
Version: 2.0.0

This test suite ensures the admin chat stream can handle complex, long, and
potentially problematic questions gracefully by using the POST method.
"""


def test_chat_stream_handles_complex_question_via_post(
    admin_user, client, admin_auth_headers, mock_ai_client_global
):
    """
    Tests that a complex, multi-part question is handled correctly via a POST request.
    """
    complex_question = "Please explain the project structure, the different files, and how the database system works."

    # Configure global mock for this specific test behavior
    async def mock_stream_chat(messages):
        """Simulated stream that echoes parts of the complex question."""
        question = messages[0]["content"] if messages else ""

        if "database system" in str(question):
            yield {"role": "assistant", "content": "Acknowledged database query. "}
        elif "project structure" in str(question):
            yield {"role": "assistant", "content": "Analyzing project structure."}
        else:
            yield {"role": "assistant", "content": "Understood long question. "}

    mock_ai_client_global.stream_chat = mock_stream_chat

    response = client.post(
        "/admin/api/chat/stream",
        json={"question": complex_question},
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    lines = [line for line in response.text.strip().split("\n") if line]
    assert len(lines) > 0


def test_chat_stream_handles_long_question_via_post(
    admin_user, client, admin_auth_headers, mock_ai_client_global
):
    """
    Tests that a very long question is handled correctly without errors via a POST request.
    """
    long_question = ("Explain " + ("the project " * 500)).strip()

    # Default global mock behavior is sufficient (returns "Mocked response")

    response = client.post(
        "/admin/api/chat/stream",
        json={"question": long_question},
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]

    lines = [line for line in response.text.strip().split("\n") if line]
    assert len(lines) > 0
