from app.services.chat.context import ChatContext
from app.services.chat.handlers.strategy_handlers import (
    CodeSearchHandler,
    DeepAnalysisHandler,
    DefaultChatHandler,
    FileReadHandler,
    FileWriteHandler,
    HelpHandler,
    MissionComplexHandler,
    ProjectIndexHandler,
)
from app.services.chat.intent_detector import ChatIntent, IntentDetector, IntentResult
from app.services.chat.security import ErrorSanitizer, PathValidator

# Re-export legacy/telemetry if needed, or deprecate
from functools import lru_cache
from typing import TYPE_CHECKING
from app.services.chat.telemetry import ChatTelemetry

if TYPE_CHECKING:
    from app.services.chat.orchestrator import ChatOrchestrator


@lru_cache
def get_chat_orchestrator() -> "ChatOrchestrator":
    """
    Returns the singleton instance of the new Strategy-based Orchestrator.
    Maintains the same function signature name as the legacy service for compatibility.
    Uses lru_cache for lazy singleton behavior.
    """
    from app.services.chat.orchestrator import ChatOrchestrator
    return ChatOrchestrator()


__all__ = [
    "ChatContext",
    "ChatIntent",
    # "ChatOrchestrator",  # Removed to prevent circular imports; use get_chat_orchestrator()
    "ChatTelemetry",
    "CodeSearchHandler",
    "DeepAnalysisHandler",
    "DefaultChatHandler",
    "ErrorSanitizer",
    "FileReadHandler",
    "FileWriteHandler",
    "HelpHandler",
    "IntentDetector",
    "IntentResult",
    "MissionComplexHandler",
    "PathValidator",
    "ProjectIndexHandler",
    "get_chat_orchestrator",
]
