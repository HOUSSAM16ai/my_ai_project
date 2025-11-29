from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_stream_is_real_implementation():
    """
    Verifies that the /admin/api/chat/stream endpoint is the real implementation
    and not a stub. The real implementation requires authentication, so a request
    without headers should return 401 Unauthorized.

    The stub implementation (the bug) allowed unauthenticated access and returned
    fake data for specific trigger questions.
    """
    # Try to hit the endpoint without auth headers
    response = client.post(
        "/admin/api/chat/stream",
        json={"question": "trigger empty stream", "conversation_id": "test_123"},
    )

    # If the stub is active (BUG), it returns 200 OK.
    # If the real implementation is active (FIXED), it returns 401 Unauthorized.
    assert response.status_code == 401, (
        f"Expected 401 Unauthorized, but got {response.status_code}. The stub implementation might still be active."
    )
