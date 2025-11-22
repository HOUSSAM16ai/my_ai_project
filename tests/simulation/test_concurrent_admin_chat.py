# tests/simulation/test_concurrent_admin_chat.py
import asyncio
import pytest
from httpx import AsyncClient
from app.main import kernel
from app.core.security import generate_service_token
from sqlalchemy import select
from app.models import AdminConversation, AdminMessage
from app.core.database import get_db
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_concurrent_chat_requests(admin_user):
    """
    Simulate concurrent chat requests to verify database stability and correctness.
    """
    # Prepare user and token
    user_id = admin_user.id
    token = generate_service_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    # Override dependency to use a NEW session for each request, matching the real app behavior
    async def override_get_db():
        async with TestingSessionLocal() as session:
             yield session

    kernel.app.dependency_overrides[get_db] = override_get_db

    try:
        async def send_chat_request(i: int):
            async with AsyncClient(app=kernel.app, base_url="http://test") as ac:
                response = await ac.post(
                    "/admin/api/chat/stream",
                    json={"question": f"Concurrent Request {i}"},
                    headers=headers,
                    timeout=10.0
                )
                return response

        # Run 5 concurrent requests
        tasks = [send_chat_request(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # Verify all succeeded
        for r in responses:
            assert r.status_code == 200
            assert "data: " in r.text

        # Verify DB State
        # We need a session to check results
        async with TestingSessionLocal() as check_session:
            stmt = select(AdminConversation).where(AdminConversation.user_id == user_id)
            result = await check_session.execute(stmt)
            conversations = result.scalars().all()

            titles = [c.title for c in conversations]
            for i in range(5):
                expected_title = f"Concurrent Request {i}"
                # We check if AT LEAST one conversation exists with this title
                # (We use 'in' because there might be other data)
                assert any(t == expected_title for t in titles)

            # Check messages
            stmt = select(AdminMessage)
            result = await check_session.execute(stmt)
            messages = result.scalars().all()

            # Filter by the conversations we just created
            created_conv_ids = [c.id for c in conversations if c.title.startswith("Concurrent Request")]

            count = 0
            for m in messages:
                if m.conversation_id in created_conv_ids:
                    count += 1

            # 5 requests * 2 messages (user + assistant) = 10
            assert count == 10

    finally:
        kernel.app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_invalid_auth_scenarios():
    """
    Test various invalid auth scenarios.
    """
    # No DB needed really, but if it hits it...
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    kernel.app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(app=kernel.app, base_url="http://test") as ac:
            # 1. No Header
            resp = await ac.post("/admin/api/chat/stream", json={"question": "Hi"})
            assert resp.status_code == 401

            # 2. Bad Token
            resp = await ac.post(
                "/admin/api/chat/stream",
                json={"question": "Hi"},
                headers={"Authorization": "Bearer invalidtoken"}
            )
            assert resp.status_code == 401
    finally:
        kernel.app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_invalid_conversation_id(admin_user):
    """
    Test providing an invalid conversation ID (non-integer or non-existent).
    """
    user_id = admin_user.id
    token = generate_service_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    kernel.app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(app=kernel.app, base_url="http://test") as ac:
            # 1. Non-integer ID
            resp = await ac.post(
                "/admin/api/chat/stream",
                json={"question": "Hi", "conversation_id": "invalid-id"},
                headers=headers
            )
            assert resp.status_code == 200

            # 2. Non-existent Integer ID
            resp = await ac.post(
                "/admin/api/chat/stream",
                json={"question": "Hi", "conversation_id": "999999"},
                headers=headers
            )
            assert resp.status_code == 200
    finally:
        kernel.app.dependency_overrides.clear()
