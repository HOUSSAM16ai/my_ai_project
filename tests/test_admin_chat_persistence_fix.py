
import asyncio
import json
import pytest
from httpx import AsyncClient
from app.models import AdminConversation, AdminMessage, User, MessageRole
from sqlalchemy import select
from app.main import kernel
from app.core.ai_gateway import get_ai_client
from app.core.database import get_db
from tests.conftest import TestingSessionLocal
from unittest.mock import MagicMock, patch

# Override get_db to ensure we use the same engine/session factory as the test fixtures
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_admin_chat_persistence_fix(
    async_client: AsyncClient,
    db_session,
    admin_auth_headers,
    admin_user
):
    """
    Test that admin chat persists the assistant message correctly after streaming.
    This simulates the happy path but verifies the fix where we use a fresh session
    in the finally block to ensure persistence even if the request session is closed.
    """

    # Apply override to async_client's app
    kernel.app.dependency_overrides[get_db] = override_get_db

    # Patch the async_session_factory used in the admin router
    # This is necessary because the router imports it directly, and in tests
    # we need it to use the TestingSessionLocal bound to the in-memory test DB.
    # Without this patch, the code would try to use the default engine which points to a fresh in-memory DB.
    with patch("app.api.routers.admin.async_session_factory", TestingSessionLocal):
        try:
            # Mock AI client to simulate a stream
            mock_gateway = MagicMock()

            async def mock_stream_chat(messages):
                # Simulate a few chunks
                chunks = [
                    {"choices": [{"delta": {"content": "Hello"}}]},
                    {"choices": [{"delta": {"content": " "}}]},
                    {"choices": [{"delta": {"content": "World"}}]},
                    {"choices": [{"delta": {"content": "!"}}]},
                ]
                for chunk in chunks:
                    await asyncio.sleep(0.01) # Small delay to simulate network
                    yield chunk

            mock_gateway.stream_chat = mock_stream_chat

            # Override dependency
            def mock_get_client():
                return mock_gateway

            kernel.app.dependency_overrides[get_ai_client] = mock_get_client

            # 1. Start a new conversation
            payload = {"question": "Hello AI"}

            # We use the async client to make the request
            response = await async_client.post(
                "/admin/api/chat/stream",
                json=payload,
                headers=admin_auth_headers
            )

            assert response.status_code == 200

            # Read the stream content
            content = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        # Handle conversation_init vs chunks
                        if "conversation_id" in data:
                            conversation_id = data["conversation_id"]
                        elif "choices" in data:
                            content += data["choices"][0]["delta"]["content"]
                    except:
                        pass

            # 2. Check Database for Persistence
            # Check Conversation
            stmt = select(AdminConversation).where(AdminConversation.title == "Hello AI")
            result = await db_session.execute(stmt)
            conversation = result.scalar_one_or_none()

            assert conversation is not None, "Conversation was not created"

            # Check User Message
            stmt = select(AdminMessage).where(
                AdminMessage.conversation_id == conversation.id,
                AdminMessage.role == MessageRole.USER
            )
            result = await db_session.execute(stmt)
            user_msg = result.scalar_one_or_none()

            assert user_msg is not None, "User message not saved"
            assert user_msg.content == "Hello AI"

            # Check Assistant Message - THIS IS THE CRITICAL CHECK
            stmt = select(AdminMessage).where(
                AdminMessage.conversation_id == conversation.id,
                AdminMessage.role == MessageRole.ASSISTANT
            )
            result = await db_session.execute(stmt)
            assistant_msg = result.scalar_one_or_none()

            # If the bug exists (race condition or closed session), this might fail
            # or logging might show "Failed to save assistant message"
            assert assistant_msg is not None, "Assistant message was NOT saved (Bug reproduced)"
            assert assistant_msg.content == "Hello World!", f"Assistant content mismatch. Got: {assistant_msg.content}"

        finally:
            kernel.app.dependency_overrides.clear()
