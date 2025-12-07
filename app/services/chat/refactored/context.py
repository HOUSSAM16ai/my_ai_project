"""
Chat context for intent handlers.
"""

from dataclasses import dataclass, field
from typing import Any
from typing import Any as AIClient  # Placeholder for AI client type


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

    def with_param(self, key: str, value: Any) -> "ChatContext":
        """Add parameter (fluent interface)."""
        self.params[key] = value
        return self

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get parameter with default."""
        return self.params.get(key, default)
