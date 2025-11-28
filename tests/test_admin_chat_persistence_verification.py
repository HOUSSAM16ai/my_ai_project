
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.api.routers.admin import ChatRequest, chat_stream
from app.models import AdminConversation, AdminMessage
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_admin_chat_persistence_verification(db_session, caplog):
    """
    Verifies that the assistant message is correctly persisted using the injected session factory,
    and that no errors are logged during the process.
    """

    # Mock dependencies
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Mock result for get conversation
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    # Mock AI Client
    mock_ai_client = MagicMock()
    async def mock_ai_gen(messages):
        yield {"choices": [{"delta": {"content": "Hello "}}]}
        yield {"choices": [{"delta": {"content": "World"}}]}
    mock_ai_client.stream_chat = mock_ai_gen

    request = ChatRequest(question="Test Question")

    # Mock DB Add side effect to set ID
    def mock_add(obj):
        if isinstance(obj, AdminConversation):
            obj.id = 1
    mock_db.add.side_effect = mock_add

    # Create a mock session for the factory to return
    # We want to verify that THIS session is used for the assistant message
    mock_fresh_session = AsyncMock(spec=AsyncSession)
    mock_fresh_session_factory = MagicMock(return_value=mock_fresh_session)

    # Setup context manager behavior for the session
    mock_fresh_session.__aenter__.return_value = mock_fresh_session
    mock_fresh_session.__aexit__.return_value = None

    # Execute
    response = await chat_stream(
        chat_request=request,
        ai_client=mock_ai_client,
        db=mock_db,
        user_id=1,
        session_factory=mock_fresh_session_factory
    )

    # Consume stream fully to trigger safe_persist
    try:
        async for _ in response.body_iterator:
            pass
    except Exception:
        pass

    # VERIFICATION 1: Check that no error was logged
    # The previous code printed "Failed to save assistant message" to stdout.
    # The new code logs to error. We check caplog.
    for record in caplog.records:
        assert "Failed to save assistant message" not in record.message

    # VERIFICATION 2: Check that the fresh session was used to add the assistant message
    assert mock_fresh_session.add.called
    added_obj = mock_fresh_session.add.call_args[0][0]

    assert isinstance(added_obj, AdminMessage)
    assert added_obj.role == "assistant"
    # content should be the joined chunks "Hello World"
    assert added_obj.content == "Hello World"
    assert added_obj.conversation_id == 1

    # Verify commit was called
    assert mock_fresh_session.commit.called
