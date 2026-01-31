from functools import lru_cache

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
from app.services.chat.orchestrator import ChatOrchestrator
from app.services.chat.security import ErrorSanitizer, PathValidator
from app.services.chat.telemetry import ChatTelemetry

# Re-export legacy/telemetry if needed, or deprecate


@lru_cache
def get_chat_orchestrator() -> ChatOrchestrator:
    """
    Returns the singleton instance of the new Strategy-based Orchestrator.
    Maintains the same function signature name as the legacy service for compatibility.
    Using @lru_cache to ensure lazy loading and singleton behavior.
    """
    return ChatOrchestrator()


__all__ = [
    "ChatContext",
    "ChatIntent",
    "ChatOrchestrator",
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
