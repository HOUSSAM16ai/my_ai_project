"""
Agent Interface.
----------------
Defines the contract for conversational agents.
"""

from collections.abc import AsyncGenerator
from typing import Any, Protocol


class Agent(Protocol):
    """
    Protocol for a conversational agent.
    """

    async def run(
        self, question: str, context: dict[str, Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """Run the agent loop."""
        ...
