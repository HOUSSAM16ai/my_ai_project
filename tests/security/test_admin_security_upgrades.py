import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import generate_service_token
from app.models import AdminConversation, User


@pytest.mark.asyncio
async def test_access_control_isolation(
    async_client: AsyncClient,
    db_session,
):
    # 1. Setup Users Manually
    user_a = User(email="user_a@test.com", full_name="User A", is_admin=False)
    user_b = User(email="user_b@test.com", full_name="User B", is_admin=False)
    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    token_a = generate_service_token(str(user_a.id))
    token_b = generate_service_token(str(user_b.id))

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. User A creates a conversation
    resp = await async_client.post(
        "/admin/api/chat/stream", json={"question": "Hello form User A"}, headers=headers_a
    )
    # Stream response, we just want to ensure it started
    assert resp.status_code == 200

    # Get conversation ID
    result = await db_session.execute(
        select(AdminConversation).where(AdminConversation.user_id == user_a.id)
    )
    conv = result.scalars().first()
    assert conv is not None
    conv_id = conv.id

    # 3. User B tries to access User A's conversation
    # Use get_conversation endpoint
    resp_b = await async_client.get(f"/admin/api/conversations/{conv_id}", headers=headers_b)

    # Should be 404 (Not Found) because currently it filters by user_id
    assert resp_b.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_access_any_conversation(
    async_client: AsyncClient, db_session, admin_user, admin_auth_headers
):
    """
    Verifies that an Admin user can access a regular user's conversation.
    Currently, this fails (returns 404) because the query restricts by user_id.
    """
    # 1. User A creates a conversation
    user_a = User(email="user_a_secret@test.com", full_name="User A Secret", is_admin=False)
    db_session.add(user_a)
    await db_session.commit()
    await db_session.refresh(user_a)

    token_a = generate_service_token(str(user_a.id))
    headers_a = {"Authorization": f"Bearer {token_a}"}

    await async_client.post(
        "/admin/api/chat/stream", json={"question": "User A secret plan"}, headers=headers_a
    )

    result = await db_session.execute(
        select(AdminConversation).where(AdminConversation.user_id == user_a.id)
    )
    conv = result.scalars().first()
    assert conv is not None

    # 2. Admin tries to access it
    resp_admin = await async_client.get(
        f"/admin/api/conversations/{conv.id}", headers=admin_auth_headers
    )

    # Current behavior is 404. We assert 200 because that's the desired "Superhuman" state.
    # This assertion ensures the test fails NOW so we can fix it.
    assert resp_admin.status_code == 200, f"Admin got {resp_admin.status_code}, expected 200"


@pytest.mark.asyncio
async def test_cors_strictness_mock(test_app):
    middleware_names = [m.cls.__name__ for m in test_app.user_middleware]
    assert "CORSMiddleware" in middleware_names
