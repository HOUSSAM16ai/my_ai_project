import pytest
import asyncio
import json
from sqlalchemy import select, func
from app.models import AdminConversation, AdminMessage, MessageRole
from app.core.database import get_db
from tests.conftest import TestingSessionLocal

# Override get_db to ensure we use the same engine/session factory as the test fixtures
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_admin_chat_persistence_repro(async_client, admin_user, admin_auth_headers, db_session):
    from app.main import kernel

    # Apply override to async_client's app
    kernel.app.dependency_overrides[get_db] = override_get_db

    # 1. Count existing messages
    initial_msg_count = (await db_session.execute(select(func.count(AdminMessage.id)))).scalar()

    # 2. Send chat request
    # We need to stream the response to ensure the generator runs to completion
    async with async_client.stream(
        "POST",
        "/admin/api/chat/stream",
        json={"question": "Test Persistence", "conversation_id": None},
        headers=admin_auth_headers
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            pass # Consume stream

    # 3. Verify Persistence

    # Check if conversation was created
    stmt = select(AdminConversation).where(AdminConversation.user_id == admin_user.id)
    result = await db_session.execute(stmt)
    conversation = result.scalar_one_or_none()

    assert conversation is not None, "Conversation was not created"

    # Check if messages were created
    # Should have 2: User message and Assistant message
    stmt_msgs = select(AdminMessage).where(AdminMessage.conversation_id == conversation.id)
    result_msgs = await db_session.execute(stmt_msgs)
    messages = result_msgs.scalars().all()

    assert len(messages) == 2, f"Expected 2 messages, found {len(messages)}"

    user_msg = next((m for m in messages if m.role == MessageRole.USER), None)
    assist_msg = next((m for m in messages if m.role == MessageRole.ASSISTANT), None)

    assert user_msg is not None
    assert user_msg.content == "Test Persistence"

    assert assist_msg is not None, "Assistant message was not persisted!"
    # The mock returns "Mocked response" (from mock_ai_client_global)
    assert assist_msg.content == "Mocked response"

    # Cleanup
    kernel.app.dependency_overrides.clear()
