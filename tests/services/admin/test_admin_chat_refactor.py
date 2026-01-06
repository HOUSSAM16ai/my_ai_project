from unittest.mock import AsyncMock

import pytest

from app.core.domain.models import AdminConversation, MessageRole, User
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService


@pytest.mark.asyncio
async def test_admin_chat_refactor_structure():
    """
    Verifies that the refactored service delegates correctly to its components.
    """
    mock_db = AsyncMock()
    service = AdminChatBoundaryService(mock_db)

    # Check if components are initialized
    assert service.persistence is not None
    assert service.streamer is not None

    # Mock the persistence layer
    service.persistence.get_or_create_conversation = AsyncMock()
    service.persistence.get_or_create_conversation.return_value = AdminConversation(
        id=1, title="Test"
    )

    # Call the facade method
    actor = User(id=1, email="admin@example.com", full_name="Admin", is_admin=True)
    result = await service.get_or_create_conversation(actor, "hello")

    # Verify delegation
    service.persistence.get_or_create_conversation.assert_called_once_with(actor.id, "hello", None)
    assert result.id == 1


@pytest.mark.asyncio
async def test_admin_chat_persistence_delegation():
    """
    Verifies message saving delegation.
    """
    mock_db = AsyncMock()
    service = AdminChatBoundaryService(mock_db)

    service.persistence.save_message = AsyncMock()

    await service.save_message(1, MessageRole.USER, "hi")

    service.persistence.save_message.assert_called_once_with(1, MessageRole.USER, "hi")
