from functools import lru_cache
from typing import TYPE_CHECKING

from app.services.chat.context import ChatContext
from app.services.chat.intent_detector import ChatIntent, IntentResult
from app.services.chat.telemetry import ChatTelemetry

if TYPE_CHECKING:
    from app.services.chat.orchestrator import ChatOrchestrator

# Re-export legacy/telemetry if needed, or deprecate


@lru_cache
def get_chat_orchestrator() -> "ChatOrchestrator":
    """
    Returns the singleton instance of the new Strategy-based Orchestrator.
    Maintains the same function signature name as the legacy service for compatibility.
    Using @lru_cache to ensure lazy loading and singleton behavior.
    """
    from app.services.chat.orchestrator import ChatOrchestrator

    return ChatOrchestrator()


__all__ = [
    "ChatContext",
    "ChatIntent",
    "ChatTelemetry",
    "IntentResult",
    "get_chat_orchestrator",
]
