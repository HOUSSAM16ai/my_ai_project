"""
Chat context for intent handlers.
"""
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

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
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Factory to create new DB sessions for background tasks
    session_factory: Callable[[], AsyncSession] | None = None

    def get_param(self, key: str, default: Any=None) -> Any:
        """Get parameter with default."""
        return self.params.get(key, default)
