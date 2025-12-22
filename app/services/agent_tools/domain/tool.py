"""
Standard Agent Tool Implementation (Domain Layer).
Adheres to AgentTool Protocol.
"""
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class StandardTool:
    """
    A concrete implementation of AgentTool.
    Uses the Strategy Pattern for the handler.
    """
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]

    async def execute(self, **kwargs) -> Any:
        return await self.handler(**kwargs)
