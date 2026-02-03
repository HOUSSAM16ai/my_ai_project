"""
Agent Interface.
----------------
Defines the contract for conversational agents.
"""

from typing import Protocol, AsyncGenerator, Any

class Agent(Protocol):
    """
    Protocol for a conversational agent.
    """

    async def run(
        self,
        question: str,
        context: dict[str, Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """Run the agent loop."""
        ...
