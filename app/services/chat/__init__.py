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

# Re-export legacy/telemetry if needed, or deprecate
from app.services.chat.telemetry import ChatTelemetry

# Singleton Instance
_orchestrator_instance = ChatOrchestrator()


def get_chat_orchestrator() -> ChatOrchestrator:
    """
    Returns the singleton instance of the new Strategy-based Orchestrator.
    Maintains the same function signature name as the legacy service for compatibility.
    """
    return _orchestrator_instance


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
