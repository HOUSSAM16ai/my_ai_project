"""
Tool builder with fluent interface.

BEFORE: Complex decorator with CC = 25
AFTER: Simple builder with CC = 2
"""
from typing import Any

from collections.abc import Callable

from app.core.patterns.builder import FluentBuilder
from app.services.agent_tools.tool_model import Tool, ToolConfig

class ToolBuilder(FluentBuilder[Tool]):
    """
    Builder for creating tools with fluent interface.

    Complexity: 2 (down from 25 in decorator)
    """

    def __init__(self, name: str):
        self._config = ToolConfig(name=name, description='')
        super().__init__()

    def reset(self) -> None:
        """Reset builder."""
        if hasattr(self, '_config'):
            name = self._config.name
            self._config = ToolConfig(name=name, description='')

    def with_description(self, description: str) -> 'ToolBuilder':
        """Set description."""
        self._config.description = description
        return self

    def with_parameters(self, parameters: dict[str, Any]) -> 'ToolBuilder':
        """Set parameters schema."""
        self._config.parameters = parameters
        return self

    def with_category(self, category: str) -> 'ToolBuilder':
        """Set category."""
        self._config.category = category
        return self

    def with_aliases(self, aliases: list[str]) -> 'ToolBuilder':
        """Set aliases."""
        self._config.aliases = aliases
        return self

    def with_capabilities(self, capabilities: list[str]) -> 'ToolBuilder':
        """Set capabilities."""
        self._config.capabilities = capabilities
        return self

    def allow_disable(self, allow: bool = True) -> 'ToolBuilder':
        """Set if tool can be disabled."""
        self._config.allow_disable = allow
        return self

    def with_handler(self, handler: Callable) -> 'ToolBuilder':
        """Set handler function."""
        self._config.handler = handler
        return self

    def build(self) -> Tool:
        """Build tool."""
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Invalid tool configuration: {', '.join(errors)}")
        return Tool(config=self._config)
