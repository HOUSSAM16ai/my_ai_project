import pytest
from sqlalchemy import select
from app.models import AdminConversation, AdminMessage

@pytest.mark.asyncio
async def test_admin_chat_persistence_success(client, db_session, admin_auth_headers):
    """
    Test that the admin chat endpoint correctly persists conversations and messages.
    """
    # 1. Send a request to the admin chat endpoint with AUTH
    response = client.post(
        "/admin/api/chat/stream",
        json={"question": "Hello, verify persistence!"},
        headers=admin_auth_headers
    )

    assert response.status_code == 200

    # Consume the stream to ensure the generator runs and persistence happens
    content = response.text
    assert "data: " in content

    # 2. Verify that a conversation WAS created
    stmt = select(AdminConversation)
    result = await db_session.execute(stmt)
    conversations = result.scalars().all()
    assert len(conversations) == 1, "Fix failed: Conversation was NOT created"
    assert conversations[0].title == "Hello, verify persistence!"

    # 3. Verify that messages WERE created
    stmt = select(AdminMessage).where(AdminMessage.conversation_id == conversations[0].id)
    result = await db_session.execute(stmt)
    messages = result.scalars().all()

    # Expecting at least 2 messages: User and Assistant
    # Note: The mock AI client yields {"role": "assistant", "content": "Mocked response"}
    # My code extracts 'content' from that.
    assert len(messages) >= 2, f"Fix failed: Expected 2+ messages, found {len(messages)}"

    user_msg = next(m for m in messages if m.role == "user")
    assert user_msg.content == "Hello, verify persistence!"

    asst_msg = next(m for m in messages if m.role == "assistant")
    assert asst_msg.content == "Mocked response"
