import pytest
from datetime import datetime
from sqlmodel import select
from app.models import AdminConversation, User
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_latest_chat_determinism(async_client: AsyncClient, admin_user: User, db_session: AsyncSession):
    """
    Verifies that get_latest_chat returns the conversation with the higher ID
    when multiple conversations exist with the exact same timestamp.
    """
    # Create two conversations with the SAME timestamp
    now = datetime.utcnow()

    # Create first conversation
    conv1 = AdminConversation(
        user_id=admin_user.id,
        title="Conversation 1",
        created_at=now,
        updated_at=now
    )
    db_session.add(conv1)
    await db_session.flush() # ensure ID is assigned

    # Create second conversation - this should have a higher ID
    conv2 = AdminConversation(
        user_id=admin_user.id,
        title="Conversation 2",
        created_at=now,
        updated_at=now
    )
    db_session.add(conv2)
    await db_session.flush()

    await db_session.commit()

    conv1_id = conv1.id
    conv2_id = conv2.id

    # Verify IDs are as expected (conv2 should be higher/newer)
    assert conv2_id > conv1_id

    # Get the admin token
    from app.core.security import generate_service_token
    token = generate_service_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/admin/api/chat/latest", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # The bug is that it might return conv1 because timestamps are equal.
    # We expect conv2 because it has the higher ID.
    # The response payload has 'conversation_id' not 'id'
    assert data["conversation_id"] == conv2_id, f"Expected conversation {conv2_id} (higher ID), but got {data['conversation_id']}"
