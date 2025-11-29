import json

import pytest

from app.core.database import get_db
from tests.conftest import TestingSessionLocal


# Override get_db to ensure we use the same engine/session factory as the test fixtures
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_admin_chat_returns_conversation_init_event(
    async_client, admin_user, admin_auth_headers, db_session
):
    """
    Regression test: Ensure that the admin chat stream starts with a 'conversation_init' event.
    This is critical for the frontend to know the conversation ID immediately, especially for new conversations.
    """
    from app.main import kernel

    # Apply override to async_client's app
    kernel.app.dependency_overrides[get_db] = override_get_db

    # 1. Send chat request with a non-existent conversation ID
    # This forces the server to create a new conversation
    non_existent_id = "999999"

    found_init_event = False
    new_conversation_id = None
    new_conversation_title = None

    async with async_client.stream(
        "POST",
        "/admin/api/chat/stream",
        json={"question": "New conversation please", "conversation_id": non_existent_id},
        headers=admin_auth_headers,
    ) as response:
        assert response.status_code == 200

        async for line in response.aiter_lines():
            if not line:
                continue

            # Check for the specific event line
            if line == "event: conversation_init":
                found_init_event = True
                continue

            # If we found the event, the next data line should contain the payload
            if found_init_event and line.startswith("data: "):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    if "conversation_id" in data:
                        new_conversation_id = data.get("conversation_id")
                        new_conversation_title = data.get("title")
                        # We found the init payload, we can stop checking lines for this purpose
                        # But we continue loop to consume stream fully
                        found_init_event = False
                except json.JSONDecodeError:
                    pass

    # Assertions
    # Note: found_init_event is set to False after finding the data, so we check new_conversation_id instead
    assert new_conversation_id is not None, (
        "The init event payload did not contain 'conversation_id'."
    )
    assert new_conversation_title is not None, "The init event payload did not contain 'title'."
    assert new_conversation_id != int(non_existent_id), "The server should have generated a new ID."

    # Cleanup
    kernel.app.dependency_overrides.clear()
