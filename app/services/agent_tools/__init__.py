from .core import (
    get_tool,
    get_tools_schema,
    has_tool,
    list_tools,
    resolve_tool_name,
    tool,
)
from .definitions import ToolResult
from .registry import ToolRegistry, get_tool_registry
from .tool_model import Tool as AgentTool, ToolConfig

# Alias for backward compatibility if needed, or simplification
get_registry = get_tool_registry

__all__ = [
    "AgentTool",
    "ToolConfig",
    "ToolResult",
    "ToolRegistry",
    "get_registry",
    "get_tool_registry",
    "get_tool",
    "get_tools_schema",
    "has_tool",
    "list_tools",
    "resolve_tool_name",
    "tool",
]
