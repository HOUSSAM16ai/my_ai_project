"""
LLM Client Interface (ISP).
---------------------------
Defines the contract for any Large Language Model provider.
"""

from collections.abc import AsyncGenerator
from typing import Any, Protocol, runtime_checkable

from app.core.types import JSONDict


@runtime_checkable
class LLMClient(Protocol):
    """
    Protocol defining the interface for AI Clients.
    Follows ISP: only essential methods for interaction.
    """

    async def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]:
        """Stream a chat conversation."""
        ...

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str:
        """Send a single message and get the full response string."""
        ...

    # Legacy support (can be deprecated later)
    async def generate_text(self, prompt: str, **kwargs) -> Any:
        """Generate text helper."""
        ...

    async def forge_new_code(self, **kwargs) -> Any:
        """Code generation helper."""
        ...
