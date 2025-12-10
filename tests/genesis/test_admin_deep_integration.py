"""
Test Deep Integration of Genesis into Admin Chat.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.chat.intent import ChatIntent, IntentResult
from app.services.chat.service import ChatOrchestratorService

@pytest.fixture
def mock_genesis():
    # Patch the CLASS where it is DEFINED, because the handler imports it inside the function
    with patch("app.genesis.core.GenesisAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run.return_value = "Found FIXME in app/core/test.py at line 10"
        yield instance

@pytest.mark.asyncio
async def test_admin_deep_analysis_flow(mock_genesis):
    """
    Verifies that asking about 'bugs' triggers Genesis.
    """
    orchestrator = ChatOrchestratorService()

    # Mock Intent Detection to force DEEP_ANALYSIS
    intent_result = IntentResult(
        intent=ChatIntent.DEEP_ANALYSIS,
        confidence=0.9,
        params={"question": "Where are the bugs?"},
        reasoning="Testing"
    )

    with patch.object(orchestrator, 'detect_intent', return_value=intent_result):
        # Run
        chunks = []
        async for chunk in orchestrator.orchestrate(
            "Where are the bugs?",
            user_id=1,
            conversation_id=1,
            ai_client=MagicMock(),
            history_messages=[]
        ):
            chunks.append(chunk)

        full_response = "".join(chunks)

        # Verify Genesis was initialized and run
        # Since the handler instantiates GenesisAgent(), our mock class should be called
        assert "Found FIXME" in full_response
        assert "Genesis Analysis Started" in full_response

@pytest.mark.asyncio
async def test_intent_detection_patterns():
    from app.services.chat.intent import IntentDetector

    # Test Arabic Pattern for bugs
    res = IntentDetector.detect("أين توجد الأخطاء في الكود؟")
    assert res.intent == ChatIntent.DEEP_ANALYSIS

    # Test English Pattern for grep
    res = IntentDetector.detect("find 'TODO' in app/")
    assert res.intent == ChatIntent.CODE_SEARCH
