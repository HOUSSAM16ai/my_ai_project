from unittest.mock import MagicMock

import pytest

from app.core.ai_gateway import get_ai_client
from app.core.database import get_db
from app.models import AdminMessage, MessageRole
from tests.conftest import TestingSessionLocal


# Override get_db to ensure we use the same engine/session factory as the test fixtures
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


# Mock AI client that yields nothing (empty stream)
async def mock_empty_stream(messages):
    if False:
        yield "nothing"


@pytest.mark.asyncio
async def test_admin_chat_empty_response_persistence(
    async_client, admin_user, admin_auth_headers, db_session
):
    """
    Test that an empty response from the AI is handled gracefully.
    Ideally, we should probably save an error message or something indicating failure,
    or at least ensure the system doesn't break.

    Current behavior: If response is empty, nothing is saved.
    We want to verify this behavior or identify it as a bug if we expect an error message.
    """
    from unittest.mock import patch

    from app.main import kernel

    # Apply override to async_client's app
    kernel.app.dependency_overrides[get_db] = override_get_db

    # Mock the AI client to return empty stream
    mock_gateway = MagicMock()
    mock_gateway.stream_chat = mock_empty_stream
    kernel.app.dependency_overrides[get_ai_client] = lambda: mock_gateway

    # CRITICAL: We must patch async_session_factory in the router module
    # because the router calls it directly in the `finally` block.
    # We patch it to return a context manager that yields a session from our TestingSessionLocal
    # BUT, async_session_factory() is a function that returns an async context manager.

    # Let's create a helper that mimics the factory behavior but uses TestingSessionLocal
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session_factory():
        async with TestingSessionLocal() as session:
            yield session

    # We need to patch where it is imported in admin.py
    with patch("app.api.routers.admin.async_session_factory", side_effect=mock_session_factory):
        # 1. Send chat request
        async with async_client.stream(
            "POST",
            "/admin/api/chat/stream",
            json={"question": "Test empty response"},
            headers=admin_auth_headers,
        ) as response:
            assert response.status_code == 200
            # Consume the stream
            async for _ in response.aiter_lines():
                pass

        # 2. Check what was saved in DB
        from sqlalchemy import select

        from app.models import AdminConversation

        # Get the conversation
        stmt = select(AdminConversation).where(AdminConversation.user_id == admin_user.id)
        result = await db_session.execute(stmt)
        conversations = result.scalars().all()
        assert len(conversations) > 0
        conversation = conversations[-1]

        # Get messages
        stmt = (
            select(AdminMessage)
            .where(AdminMessage.conversation_id == conversation.id)
            .order_by(AdminMessage.created_at)
        )
        result = await db_session.execute(stmt)
        messages = result.scalars().all()

        # Verify user message exists
        user_msgs = [m for m in messages if m.role == MessageRole.USER]
        assert len(user_msgs) == 1
        assert user_msgs[0].content == "Test empty response"

        # Verify assistant message exists (BUG: It currently doesn't exist)
        asst_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]

        # Asserting that we EXPECT an assistant message (error or empty)
        # If this fails, it confirms the bug that no feedback is saved.
        assert (
            len(asst_msgs) > 0
        ), "Expected an assistant message (even if empty or error) to be persisted."

        # With the fix, we expect the specific error message
        assert asst_msgs[0].content == "Error: No response received from AI service."

    # Cleanup
    kernel.app.dependency_overrides.clear()
