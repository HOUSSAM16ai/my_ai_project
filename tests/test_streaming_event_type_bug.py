
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.ai_gateway import get_ai_client
from app.core.database import get_db, async_session_factory
from app.api.routers.admin import get_current_user_id, get_session_factory
from app.models import AdminConversation, AdminMessage, MessageRole

# Mock dependencies
mock_ai_client = MagicMock()
mock_db_session = AsyncMock()

def override_get_ai_client():
    return mock_ai_client

def override_get_db():
    yield mock_db_session

def override_get_current_user_id():
    return 1

def override_get_session_factory():
    return MagicMock()

app.dependency_overrides[get_ai_client] = override_get_ai_client
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id
app.dependency_overrides[get_session_factory] = override_get_session_factory

client = TestClient(app)

@pytest.mark.asyncio
async def test_chat_stream_missing_event_type():
    """
    Verifies that the chat_stream endpoint yields 'message' events (missing 'event: ...' line)
    instead of the required 'event: delta' for content chunks.
    """
    # Setup mocks
    # Fix: properly mock execute return value for SQLAlchemy style usage
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None # No existing conversation

    mock_db_session.execute.return_value = mock_result

    # Also mock add/commit/refresh to be awaitable if needed, or just standard AsyncMock handles it

    # Mock AI response generator
    async def mock_stream_chat(messages):
        yield {"choices": [{"delta": {"content": "Hello"}}]}
        yield {"choices": [{"delta": {"content": " World"}}]}

    mock_ai_client.stream_chat.side_effect = mock_stream_chat

    # Make request
    response = client.post(
        "/admin/api/chat/stream",
        json={"question": "Test question"},
        headers={"Authorization": "Bearer test-token"} # Auth is mocked but header needed for some logic potentially
    )

    assert response.status_code == 200

    # Analyze stream content
    content = response.content.decode("utf-8")
    lines = content.split("\n\n")

    has_delta_event = False
    has_default_message_event = False

    for line in lines:
        if not line.strip():
            continue

        if "data: " in line and "Hello" in line:
            # Check if this block has "event: delta"
            if "event: delta" in line:
                has_delta_event = True
            else:
                has_default_message_event = True

    # The bug is that we expect delta events but get default message events
    # So for the BUG to be present: has_default_message_event should be True, has_delta_event should be False

    print(f"\nStream Content Sample:\n{content[:500]}...\n")

    assert has_default_message_event, "Expected default message events (bug reproduction)"
    assert not has_delta_event, "Did not expect 'event: delta' (bug reproduction)"
