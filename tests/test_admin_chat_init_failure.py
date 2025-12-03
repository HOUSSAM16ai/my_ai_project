from unittest.mock import MagicMock, patch

import pytest

from app.core.ai_gateway import AIClient
from app.models import AdminConversation
from app.services.admin_chat_boundary_service import AdminChatBoundaryService


@pytest.mark.asyncio
async def test_conversation_init_before_intent_detection_failure():
    """
    Verifies that the conversation_init event is emitted even if intent detection fails.
    This ensures the frontend has the conversation ID to handle the subsequent error gracefully.
    """
    # Setup
    db_session = MagicMock()
    service = AdminChatBoundaryService(db_session)

    user_id = 1
    conversation = AdminConversation(id=123, title="Test Conv", user_id=user_id)
    question = "Test question"
    history = []
    ai_client = MagicMock(spec=AIClient)
    session_factory = MagicMock()

    # Mock orchestrator to raise an exception during detect_intent
    with patch("app.services.admin_chat_boundary_service.get_chat_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()
        mock_orch.detect_intent.side_effect = Exception("Intent detection failed")
        mock_get_orch.return_value = mock_orch

        # Execute
        generator = service.stream_chat_response(
            user_id, conversation, question, history, ai_client, session_factory
        )

        events = []
        try:
            async for event in generator:
                events.append(event)
        except Exception:
            pass

        # Verify
        has_init = any("conversation_init" in e for e in events)
        has_error = any("Intent detection failed" in e for e in events) or any(
            "Service Error" in e for e in events
        )

        assert has_init, "conversation_init event was not emitted before intent detection failure"
        assert has_error, "Error event was not emitted after intent detection failure"
