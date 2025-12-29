from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models import AdminConversation, AdminMessage
from app.services.users.history_service import get_recent_conversations, rate_message_in_db


class TestHistoryServiceComprehensive:
    @pytest.fixture
    async def user_with_conversations(self, db_session, user_factory, mission_factory):
        # When using pytest-factoryboy with async sessions, we need to handle creation carefully.
        # The AsyncUserFactory in conftest.py sets sqlalchemy_session to db_session.
        # However, factory_boy's .create() calls session.commit() which is a coroutine in AsyncSession.
        # It's better to build() the object and add/commit manually in the async fixture.

        user = user_factory.build()
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create conversations
        conversations = []
        for i in range(3):
            # Mission factory might not automatically set the user_id if we just pass user=user object depending on implementation
            # It seems Mission table has initiator_id which is FK to User.
            # Let's explicitly set initiator_id

            mission = mission_factory.build(initiator_id=user.id)
            db_session.add(mission)
            await db_session.commit()
            await db_session.refresh(mission)

            conversation = AdminConversation(
                user_id=user.id,
                title=f"Conversation {i}",
                conversation_type="chat",
                linked_mission_id=mission.id,
            )
            db_session.add(conversation)
            conversations.append(conversation)

        await db_session.commit()
        for c in conversations:
            await db_session.refresh(c)

        return user, conversations

    @pytest.fixture
    async def user_with_messages(self, db_session, user_with_conversations):
        user, conversations = user_with_conversations
        conversation = conversations[0]

        messages = []
        for i in range(2):
            message = AdminMessage(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
            )
            db_session.add(message)
            messages.append(message)

        await db_session.commit()
        for m in messages:
            await db_session.refresh(m)

        return user, conversation, messages

    @pytest.mark.asyncio
    async def test_get_recent_conversations_success(self, user_with_conversations, db_session):
        user, _expected_conversations = user_with_conversations

        # Use the actual db_session from fixture which is connected to the in-memory DB with tables
        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = db_session
        mock_session_ctx.__aexit__.return_value = None

        with patch("app.services.users.history_service.async_session_factory", return_value=mock_session_ctx):
            conversations = await get_recent_conversations(user.id)

            assert len(conversations) == 3
            # Check ordering (descending ID/created_at) - newest should be first
            assert conversations[0].id > conversations[1].id

    @pytest.mark.asyncio
    async def test_get_recent_conversations_limit(self, user_with_conversations, db_session):
        user, _ = user_with_conversations

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = db_session
        mock_session_ctx.__aexit__.return_value = None

        with patch("app.services.users.history_service.async_session_factory", return_value=mock_session_ctx):
            conversations = await get_recent_conversations(user.id, limit=1)

            assert len(conversations) == 1

    @pytest.mark.asyncio
    async def test_get_recent_conversations_error(self):
        with patch("app.services.users.history_service.async_session_factory") as mock_factory:
            mock_factory.side_effect = Exception("DB Connection Failed")

            conversations = await get_recent_conversations(1)
            assert conversations == []

    @pytest.mark.asyncio
    async def test_rate_message_success(self, user_with_messages, db_session):
        user, _, messages = user_with_messages
        message_to_rate = messages[0]

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = db_session
        mock_session_ctx.__aexit__.return_value = None

        with patch("app.services.users.history_service.async_session_factory", return_value=mock_session_ctx):
            result = await rate_message_in_db(message_to_rate.id, "good", user.id)

            assert result["status"] == "success"
            assert "rated as 'good'" in result["message"]

    @pytest.mark.asyncio
    async def test_rate_message_invalid_rating(self):
        result = await rate_message_in_db(1, "awesome", 1)
        assert result["status"] == "error"
        assert "Invalid rating" in result["message"]

    @pytest.mark.asyncio
    async def test_rate_message_not_found(self, user_with_messages, db_session):
        user, _, _ = user_with_messages

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = db_session
        mock_session_ctx.__aexit__.return_value = None

        with patch("app.services.users.history_service.async_session_factory", return_value=mock_session_ctx):
            result = await rate_message_in_db(999999, "good", user.id)

            assert result["status"] == "error"
            assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_rate_message_security_violation(
        self, user_with_messages, user_factory, db_session
    ):
        _user, _, messages = user_with_messages
        other_user = user_factory.build()
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        message_to_rate = messages[0]

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = db_session
        mock_session_ctx.__aexit__.return_value = None

        with patch("app.services.users.history_service.async_session_factory", return_value=mock_session_ctx):
            result = await rate_message_in_db(message_to_rate.id, "bad", other_user.id)

            assert result["status"] == "error"
            assert "Permission denied" in result["message"]

    @pytest.mark.asyncio
    async def test_rate_message_db_error(self, user_with_messages):
        user, _, messages = user_with_messages
        message_to_rate = messages[0]

        from tests.conftest import TestingSessionLocal

        # To trigger DB error, we need to force it.
        # Since 'rating' field doesn't exist, it won't call commit().
        # We need to make it believe 'rating' exists so it calls commit(),
        # OR we mock the execute to fail.

        with patch("app.services.users.history_service.async_session_factory") as mock_factory:
            session = TestingSessionLocal()
            mock_factory.return_value.__aenter__.return_value = session
            mock_factory.return_value.__aexit__.return_value = None

            # Make session.commit fail
            session.commit = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

            # We also need to patch the message object to have 'rating' attribute
            # so the code attempts to save it.
            # The code fetches message via query.
            # We can mock session.execute to return our mock message.

            mock_msg = MagicMock()
            mock_msg.id = message_to_rate.id
            mock_msg.conversation.user_id = user.id
            mock_msg.rating = None  # Exists

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_msg
            session.execute = AsyncMock(return_value=mock_result)

            result = await rate_message_in_db(message_to_rate.id, "good", user.id)
            await session.close()

            assert result["status"] == "error"
            assert "database error" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_rate_message_unexpected_error(self, user_with_messages):
        user, _, messages = user_with_messages
        message_to_rate = messages[0]

        from tests.conftest import TestingSessionLocal

        with patch("app.services.users.history_service.async_session_factory") as mock_factory:
            session = TestingSessionLocal()
            mock_factory.return_value.__aenter__.return_value = session
            mock_factory.return_value.__aexit__.return_value = None

            # Mock session.execute to raise unexpected Exception
            session.execute = AsyncMock(side_effect=Exception("Unexpected boom"))

            result = await rate_message_in_db(message_to_rate.id, "good", user.id)
            await session.close()

            assert result["status"] == "error"
            assert "unexpected error" in result["message"].lower()
