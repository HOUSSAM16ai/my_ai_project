"""
Tool definition and configuration.
"""

from typing import Any

from collections.abc import Callable
from dataclasses import dataclass, field

@dataclass
class ToolResult:
    """Standardized tool output."""
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None

@dataclass
class ToolConfig:
    """Tool configuration."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    aliases: list[str] = field(default_factory=list)
    allow_disable: bool = True
    capabilities: list[str] = field(default_factory=list)
    handler: Callable | None = None

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []

        if not self.name:
            errors.append("Tool name is required")

        if not self.description:
            errors.append("Tool description is required")

        if not self.handler:
            errors.append("Tool handler is required")

        return errors

@dataclass
class Tool:
    """Tool with execution capabilities."""

    config: ToolConfig
    is_disabled: bool = False
    execution_count: int = 0
    error_count: int = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def canonical_name(self) -> str:
        """Get canonical name (for aliases)."""
        return self.config.name

    def can_execute(self) -> bool:
        """Check if tool can be executed."""
        return not self.is_disabled and self.config.handler is not None

    async def execute(self, **kwargs) -> dict[str, str | int | bool]:
        """Execute tool."""
        if not self.can_execute():
            raise PermissionError(f"Tool '{self.name}' is disabled or has no handler")

        try:
            result = await self.config.handler(**kwargs)
            self.execution_count += 1
            return result
        except Exception:
            self.error_count += 1
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get tool statistics."""
        return {
            "name": self.name,
            "executions": self.execution_count,
            "errors": self.error_count,
            "disabled": self.is_disabled,
        }

def tool(
    name: str,
    description: str,
    category: str = "general",
    capabilities: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    aliases: list[str] | None = None,
):
    """Decorator to register a function as a tool."""
    def decorator(func):
        func._tool_config = ToolConfig(
            name=name,
            description=description,
            category=category,
            capabilities=capabilities or [],
            parameters=parameters or {},
            aliases=aliases or [],
            handler=func
        )
        return func
    return decorator
