import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import AdminConversation
from app.services.admin_chat_boundary_service import AdminChatBoundaryService
from app.services.chat_orchestrator_service import ChatIntent, IntentResult


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.SECRET_KEY = "test_secret"
    return settings


@pytest.fixture
def service(mock_settings):
    db_session = AsyncMock()
    with (
        patch("app.services.admin_chat_boundary_service.get_settings", return_value=mock_settings),
        patch("app.services.admin_chat_boundary_service.get_service_boundary"),
        patch("app.services.admin_chat_boundary_service.get_policy_boundary"),
    ):
        service = AdminChatBoundaryService(db_session)
        service.settings = mock_settings
        return service


@pytest.mark.asyncio
async def test_stream_chat_response_deep_analysis_intent(service):
    """
    Verifies that ChatIntent.DEEP_ANALYSIS triggers the orchestrator path
    and emits an 'intent' event, instead of falling back to simple chat.
    """
    user_id = 1
    conversation = AdminConversation(id=1, title="Deep Analysis Test", user_id=user_id)
    question = "explain the architecture"
    history = []

    ai_client = MagicMock()

    # Mock session factory for persistence
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.services.admin.chat_streamer.get_chat_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()

        # 1. Setup Intent Detection to return DEEP_ANALYSIS
        mock_orch.detect_intent.return_value = IntentResult(
            intent=ChatIntent.DEEP_ANALYSIS,
            confidence=0.95,
            params={"question": question},
            reasoning="Matched pattern",
        )

        # 2. Mock orchestrator.orchestrate to simulate Overmind response
        async def orchestrator_gen(*args, **kwargs):
            yield "Deep analysis in progress..."
            yield "Here is the architectural overview."

        mock_orch.orchestrate = orchestrator_gen

        # 3. Mock AI Client stream_chat (fallback path) to verify it's NOT called
        async def fallback_gen(*args, **kwargs):
            yield "This is the fallback simple chat response."

        ai_client.stream_chat = fallback_gen

        mock_get_orch.return_value = mock_orch

        # Run the stream
        generator = service.stream_chat_response(
            user_id, conversation, question, history, ai_client, mock_session_factory
        )

        events = []
        async for event in generator:
            events.append(event)

        # Parse events to check for intent
        intent_event_found = False
        fallback_content_found = False
        deep_analysis_content_found = False

        for event in events:
            if event.startswith("event: intent"):
                intent_event_found = True
                # verify payload
                payload_str = event.split("data: ")[1].strip()
                payload = json.loads(payload_str)
                assert payload["intent"] == "deep_analysis"

            if "fallback simple chat response" in event:
                fallback_content_found = True

            if "Deep analysis in progress" in event:
                deep_analysis_content_found = True

        # Assertions
        assert intent_event_found, "DEEP_ANALYSIS intent event was not emitted!"
        assert deep_analysis_content_found, "Orchestrator was not called for DEEP_ANALYSIS!"
        assert not fallback_content_found, (
            "System fell back to simple chat instead of using Orchestrator!"
        )
