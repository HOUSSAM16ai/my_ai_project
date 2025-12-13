from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.routers.admin import get_admin_service, get_current_user_id
from app.main import app
from app.services.admin_chat_boundary_service import AdminChatBoundaryService


# Mock the dependency to bypass auth
def mock_get_current_user_id():
    return 1


# Mock the service to avoid real DB calls or complex logic during schema validation check
mock_service = MagicMock(spec=AdminChatBoundaryService)
mock_service.orchestrate_chat_stream.return_value = (
    AsyncMock()
)  # Return an async generator or similar if needed


def mock_get_admin_service():
    return mock_service


app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
app.dependency_overrides[get_admin_service] = mock_get_admin_service

client = TestClient(app)


def test_chat_stream_missing_user_id_in_body():
    """
    Reproduction test for the 422 error when user_id is missing from the request body.
    Now verifying the fix (should return success, likely 200 or whatever StreamingResponse returns as headers).
    Since we mock the service to return a generator, StreamingResponse should start successfully.
    """
    response = client.post(
        "/admin/api/chat/stream",
        json={
            "question": "Hello, is this working?",
            "conversation_id": None,
            # user_id is missing
        },
    )

    # After fix, this should be 200 OK (StreamingResponse)
    print(f"Response Status: {response.status_code}")
    if response.status_code != 200:
        print(
            f"Response Body: {response.json() if response.headers.get('content-type') == 'application/json' else response.text}"
        )

    assert response.status_code == 200
