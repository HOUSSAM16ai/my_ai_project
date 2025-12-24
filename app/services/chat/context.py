"""
Chat context for intent handlers.
"""
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

# Placeholder for AIClient type
type AIClient = Any

@dataclass
class ChatContext:
    """Context passed to intent handlers."""
    question: str
    user_id: int
    conversation_id: int
    ai_client: AIClient
    history_messages: list[dict[str, str]]
    intent: str
    confidence: float
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Factory to create new DB sessions for background tasks
    session_factory: Callable[[], AsyncSession] | None = None

    def get_param(self, key: str, default: Any=None) -> Any:
        """Get parameter with default."""
        return self.params.get(key, default)
