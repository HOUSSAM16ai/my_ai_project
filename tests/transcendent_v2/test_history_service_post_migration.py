# tests/transcendent_v2/test_history_service_post_migration.py
"""
Unit test for the History Service after its migration to FastAPI async.
This test confirms the service logic works with the new async SQLAlchemy backend.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
@patch("app.services.users.history_service.async_session_factory")
async def test_rate_message_success(mock_session_factory):
    """
    Tests the successful rating of a message.
    """
    from app.services.users.history_service import rate_message_in_db

    # Arrange
    message_id = 123
    rating = "good"
    user_id = 1

    # Simulate the object returned by the database
    mock_message = MagicMock()
    mock_message.conversation.user_id = user_id
    # Add rating attribute to mock so hasattr returns True
    mock_message.rating = None

    # Setup async session mock
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_message
    mock_session.execute.return_value = mock_result

    # Setup context manager
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    # Act
    result = await rate_message_in_db(message_id, rating, user_id=user_id)

    # Assert
    assert result["status"] == "success"
    mock_session.commit.assert_called_once()
    assert mock_message.rating == rating


@pytest.mark.asyncio
@patch("app.services.users.history_service.async_session_factory")
async def test_rate_message_permission_denied(mock_session_factory):
    """
    Tests that a user cannot rate a message they don't own.
    """
    from app.services.users.history_service import rate_message_in_db

    # Arrange
    message_id = 456
    attacker_id = 999
    victim_id = 1

    mock_message = MagicMock()
    mock_message.conversation.user_id = victim_id

    # Setup async session mock
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_message
    mock_session.execute.return_value = mock_result

    # Setup context manager
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    # Act
    result = await rate_message_in_db(message_id, "bad", user_id=attacker_id)

    # Assert
    assert result["status"] == "error"
    assert "Permission denied" in result["message"]
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.users.history_service.async_session_factory")
async def test_get_recent_conversations_success(mock_session_factory):
    """
    Tests that get_recent_conversations correctly retrieves conversations.
    """
    from app.services.users.history_service import get_recent_conversations

    # Arrange
    user_id = 1
    mock_conv1 = MagicMock()
    mock_conv1.id = 1
    mock_conv2 = MagicMock()
    mock_conv2.id = 2

    # Setup async session mock
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_conv1, mock_conv2]
    mock_session.execute.return_value = mock_result

    # Setup context manager
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    # Act
    result = await get_recent_conversations(user_id, limit=5)

    # Assert
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2


@pytest.mark.asyncio
@patch("app.services.users.history_service.async_session_factory")
async def test_get_recent_conversations_returns_empty_on_error(mock_session_factory):
    """
    Tests that get_recent_conversations returns empty list on database error.
    """
    from app.services.users.history_service import get_recent_conversations

    # Arrange
    user_id = 1

    # Setup async session to raise exception
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Database error")

    # Setup context manager
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    # Act
    result = await get_recent_conversations(user_id)

    # Assert
    assert result == []
