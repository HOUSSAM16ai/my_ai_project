import pytest

from app.services.chat.intent_detector import ChatIntent
from app.services.chat.tool_router import ToolRouter


@pytest.mark.asyncio
async def test_tool_router_allows_standard_safe_intents() -> None:
    router = ToolRouter()
    decision = router.authorize_intent(role="STANDARD_USER", intent=ChatIntent.DEFAULT)

    assert decision.allowed is True
    assert decision.reason_code == "intent_allowed"


@pytest.mark.asyncio
async def test_tool_router_blocks_sensitive_intents_for_standard() -> None:
    router = ToolRouter()
    decision = router.authorize_intent(role="STANDARD_USER", intent=ChatIntent.FILE_READ)

    assert decision.allowed is False
    assert decision.reason_code == "tool_access_blocked"
    assert decision.refusal_message
