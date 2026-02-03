"""
Intent Router Interface (ISP).
------------------------------
Defines the contract for routing intents to handlers.
"""

from collections.abc import AsyncGenerator
from typing import Any, Protocol


class IntentRouter(Protocol):
    """
    Protocol for determining and executing the correct intent.
    """

    async def route_and_execute(
        self, question: str, context: dict[str, Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Analyze the question and context, route to the appropriate handler,
        and yield the response chunks.
        """
        ...
