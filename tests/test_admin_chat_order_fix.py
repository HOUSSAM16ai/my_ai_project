from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.ai_gateway import get_ai_client
from app.models import AdminConversation, AdminMessage, MessageRole, User


# Helper for async iterator
async def mock_stream_chat_generator(messages):
    yield {"choices": [{"delta": {"content": "AI"}}]}
    yield {"choices": [{"delta": {"content": " Response"}}]}


@pytest.mark.asyncio
async def test_chat_stream_message_ordering_fixed(
    client: TestClient, admin_auth_headers, db_session
):
    """
    Test that message ordering is correctly handled using ID as secondary sort key
    when timestamps are identical.
    """
    # 1. Setup - Create conversation and messages with IDENTICAL timestamps
    from sqlalchemy import select

    stmt = select(User).where(User.email == "admin@test.com")
    result = await db_session.execute(stmt)
    admin_user = result.scalar_one()

    conversation = AdminConversation(title="Test Conversation", user_id=admin_user.id)
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    # Force identical timestamps
    now = datetime.now(UTC)

    # Message 1 (Older by ID, same time)
    msg1 = AdminMessage(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content="First Message",
        created_at=now,
    )
    db_session.add(msg1)
    await db_session.commit()  # ID=1

    # Message 2 (Newer by ID, same time)
    msg2 = AdminMessage(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content="Second Message",
        created_at=now,
    )
    db_session.add(msg2)
    await db_session.commit()  # ID=2

    # 2. Request
    payload = {"question": "New Question", "conversation_id": str(conversation.id)}

    from app.main import kernel

    # Setup Mock - Use the generator function directly!
    mock_ai = MagicMock()

    call_capture = []

    async def spy_stream_chat(messages):
        call_capture.append(messages)
        async for chunk in mock_stream_chat_generator(messages):
            yield chunk

    mock_ai.stream_chat = spy_stream_chat
    kernel.app.dependency_overrides[get_ai_client] = lambda: mock_ai

    response = client.post("/admin/api/chat/stream", json=payload, headers=admin_auth_headers)

    assert response.status_code == 200
    # Consume stream
    response.read()

    # 3. Verification
    assert len(call_capture) == 1
    context_messages = call_capture[0]

    # Verify Order is Chronological (First -> Second -> New)
    assert context_messages[0]["content"] == "First Message"
    assert context_messages[1]["content"] == "Second Message"
    assert context_messages[2]["content"] == "New Question"
