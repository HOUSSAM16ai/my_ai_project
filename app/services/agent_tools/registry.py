"""
Tool registry with thread-safe operations.
"""

import logging
import threading
from typing import Any

from app.services.agent_tools.tool_model import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Thread-safe tool registry.

    Manages tool registration, lookup, and execution.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}
        self._lock = threading.RLock()

    def register(self, tool: Tool) -> None:
        """Register a tool. Complexity: 3"""
        with self._lock:
            self._validate_registration(tool)
            self._register_tool(tool)
            self._register_aliases(tool)
            logger.info(f"Tool registered: {tool.name}")

    def _validate_registration(self, tool: Tool) -> None:
        """Validate tool can be registered. Complexity: 2"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        for alias in tool.config.aliases:
            if alias in self._tools or alias in self._aliases:
                raise ValueError(f"Alias '{alias}' already registered")

    def _register_tool(self, tool: Tool) -> None:
        """Register tool in registry. Complexity: 1"""
        self._tools[tool.name] = tool

    def _register_aliases(self, tool: Tool) -> None:
        """Register tool aliases. Complexity: 1"""
        for alias in tool.config.aliases:
            self._aliases[alias] = tool.name

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        with self._lock:
            if name not in self._tools:
                raise ValueError(f"Tool '{name}' not found")
            tool = self._tools[name]
            for alias in tool.config.aliases:
                self._aliases.pop(alias, None)
            del self._tools[name]
            logger.info(f"Tool unregistered: {name}")

    def get(self, name: str) -> Tool | None:
        """Get tool by name or alias."""
        with self._lock:
            if name in self._tools:
                return self._tools[name]
            canonical = self._aliases.get(name)
            if canonical:
                return self._tools.get(canonical)
            return None

    def get_canonical_name(self, name: str) -> str | None:
        """Get canonical name for tool or alias."""
        with self._lock:
            if name in self._tools:
                return name
            return self._aliases.get(name)

    def list_tools(self, category: (str | None) = None) -> list[Tool]:
        """List all tools, optionally filtered by category."""
        with self._lock:
            tools = list(self._tools.values())
            if category:
                tools = [t for t in tools if t.config.category == category]
            return tools

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            return {
                "total_tools": len(self._tools),
                "total_aliases": len(self._aliases),
                "tools": [tool.get_stats() for tool in self._tools.values()],
            }

    def clear(self) -> None:
        """Clear all tools."""
        with self._lock:
            self._tools.clear()
            self._aliases.clear()
            logger.info("Tool registry cleared")


_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    return _global_registry
