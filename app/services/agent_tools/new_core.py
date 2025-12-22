"""
Tool Decorator for easy registration (Application Layer).
"""
from typing import Any
from collections.abc import Callable, Awaitable
from functools import wraps
from app.services.agent_tools.domain.tool import StandardTool
from app.services.agent_tools.infrastructure.registry import get_registry

def tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None
):
    """
    Decorator to register an async function as a tool.
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        registry = get_registry()

        # Create the tool instance
        t = StandardTool(
            name=name,
            description=description,
            parameters=parameters or {"type": "object", "properties": {}},
            handler=func
        )

        # Register it
        registry.register(t)

        @wraps(func)
        async def wrapper(**kwargs):
            return await func(**kwargs)

        return wrapper
    return decorator
