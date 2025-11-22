import pytest
from unittest.mock import MagicMock
import sqlalchemy as sa
from sqlalchemy import select
from app.models import AdminConversation, AdminMessage, MessageRole
from app.core.database import get_db
from app.core.ai_gateway import get_ai_client
from tests.conftest import TestingSessionLocal

# Override get_db
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_admin_chat_history_context(async_client, admin_user, admin_auth_headers, db_session):
    from app.main import kernel

    # 1. Setup Dependencies
    kernel.app.dependency_overrides[get_db] = override_get_db

    # Mock AI Client to capture called messages
    mock_gateway = MagicMock()
    captured_messages = []

    async def mock_stream_chat(messages):
        captured_messages.append(messages)
        yield {"role": "assistant", "content": "I remember."}

    mock_gateway.stream_chat = mock_stream_chat

    def mock_get_client():
        return mock_gateway

    kernel.app.dependency_overrides[get_ai_client] = mock_get_client

    # 2. Seed existing conversation and messages
    conversation = AdminConversation(
        title="History Test",
        user_id=admin_user.id
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    # Add a previous message context
    msg1 = AdminMessage(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content="My name is Jules."
    )
    msg2 = AdminMessage(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content="Hello Jules."
    )
    db_session.add(msg1)
    db_session.add(msg2)
    await db_session.commit()

    # 3. Send new question
    async with async_client.stream(
        "POST",
        "/admin/api/chat/stream",
        json={"question": "What is my name?", "conversation_id": str(conversation.id)},
        headers=admin_auth_headers
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            pass

    # 4. Verify that history was passed to AI
    # Expected: [{"role": "user", "content": "My name is Jules."}, {"role": "assistant", "content": "Hello Jules."}, {"role": "user", "content": "What is my name?"}]

    assert len(captured_messages) > 0, "AI Client was not called"
    last_call_messages = captured_messages[-1]

    # Check if history is present
    print(f"Captured Messages: {last_call_messages}")

    has_history = any(m["content"] == "My name is Jules." for m in last_call_messages)
    assert has_history, "Conversation history was NOT passed to AI client!"

    # Verify length (should be 3)
    assert len(last_call_messages) == 3

    # Cleanup
    kernel.app.dependency_overrides.clear()
