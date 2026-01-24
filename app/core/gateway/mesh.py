"""
Gateway Mesh (Legacy Facade).
-----------------------------
This module previously contained the 'NeuralRoutingMesh'.
It is now a compatibility layer pointing to the simplified `SimpleAIClient`.

Refactored for simplicity and robustness.
"""

from typing import Protocol, runtime_checkable, Any
from collections.abc import AsyncGenerator

from app.core.types import JSONDict
from app.core.gateway.simple_client import SimpleAIClient

# ============================================================================
# Legacy Aliases (For Backward Compatibility)
# ============================================================================

NeuralRoutingMesh = SimpleAIClient
"""Deprecated: Use SimpleAIClient instead."""

# ============================================================================
# Protocol Definition
# ============================================================================

@runtime_checkable
class AIClient(Protocol):
    """
    Protocol defining the interface for AI Clients.
    """
    def stream_chat(self, messages: list[JSONDict]) -> AsyncGenerator[JSONDict, None]:
        """Stream a chat conversation."""
        ...

    async def send_message(
        self, system_prompt: str, user_message: str, temperature: float = 0.7
    ) -> str:
        """Send a single message and get the full response string."""
        ...

    async def __aiter__(self):
        """Allow async iteration over the client (legacy pattern)."""
        ...

    async def generate_text(self, prompt: str, **kwargs) -> Any:
        """Legacy generation method."""
        ...

    async def forge_new_code(self, **kwargs) -> Any:
        """Legacy code generation method."""
        ...

# ============================================================================
# Factory
# ============================================================================

def get_ai_client() -> AIClient:
    """
    Factory function to get the global AI client instance.
    """
    return SimpleAIClient()
