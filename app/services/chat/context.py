"""
Chat context for intent handlers.
"""
from typing import TYPE_CHECKING
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.core.protocols import AIClientProtocol

@dataclass
class ChatContext:
    """Context passed to intent handlers."""
    question: str
    user_id: int
    conversation_id: int
    ai_client: "AIClientProtocol"
    history_messages: list[dict[str, str]]
    intent: str
    confidence: float
    params: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)

    # Factory to create new DB sessions for background tasks
    session_factory: Callable[[], AsyncSession] | None = None

    def get_param(self, key: str, default: object = None) -> object:
        """Get parameter with default."""
        return self.params.get(key, default)
