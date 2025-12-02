from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routers.admin import get_current_user_id, get_session_factory
from app.core.ai_gateway import get_ai_client
from app.core.database import get_db

# We will use the 'client' and 'test_app' fixtures provided by conftest.py
# This ensures we are testing against the correctly configured application instance.


@pytest.mark.asyncio
async def test_chat_stream_missing_event_type(client, test_app):
    """
    Verifies that the chat_stream endpoint yields 'message' events (missing 'event: ...' line)
    instead of the required 'event: delta' for content chunks.
    """

    # 1. Define Mocks
    mock_ai_client = MagicMock()
    mock_db_session = AsyncMock()

    # Mock database execution results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None  # No existing conversation
    mock_db_session.execute.return_value = mock_result

    # Mock AI response generator
    async def mock_stream_chat(messages):
        # We simulate the structure returned by many AI providers
        yield {"choices": [{"delta": {"content": "Hello"}}]}
        yield {"choices": [{"delta": {"content": " World"}}]}

    mock_ai_client.stream_chat.side_effect = mock_stream_chat

    # 2. Define Overrides
    def override_get_ai_client():
        return mock_ai_client

    async def override_get_db():
        yield mock_db_session

    def override_get_current_user_id():
        # Bypass auth validation entirely
        return 1

    def override_get_session_factory():
        # The endpoint uses session_factory() context manager
        # We need to return a factory that produces our mock_db_session
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_db_session
        mock_factory.return_value.__aexit__.return_value = None
        return mock_factory

    # 3. Apply Overrides Safely
    # Use patch.dict to modify the dependency_overrides dictionary in place,
    # and automatically restore it to its previous state (containing conftest.py overrides) upon exit.
    overrides = {
        get_ai_client: override_get_ai_client,
        get_db: override_get_db,
        get_current_user_id: override_get_current_user_id,
        get_session_factory: override_get_session_factory,
    }

    with patch.dict(test_app.dependency_overrides, overrides):
        # 4. Make Request
        response = client.post(
            "/admin/api/chat/stream",
            json={"question": "Test question"},
            headers={"Authorization": "Bearer test-token"},
        )

        # 5. Assertions
        assert response.status_code == 200, f"Response failed with: {response.text}"

        # Analyze stream content
        content = response.content.decode("utf-8")
        lines = content.split("\n\n")

        has_delta_event = False

        for line in lines:
            if not line.strip():
                continue

            # Check if this block has "event: delta" with content
            if "data: " in line and "Hello" in line and "event: delta" in line:
                has_delta_event = True

        # After the fix, we expect 'event: delta' events for content chunks
        assert has_delta_event, "Expected 'event: delta' for content chunks (fix verified)"
