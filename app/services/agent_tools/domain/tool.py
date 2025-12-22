"""
Standard Agent Tool Implementation (Domain Layer).
Adheres to AgentTool Protocol.
"""
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable, Awaitable
from app.core.protocols import AgentTool

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
