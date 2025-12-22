"""
InMemory Tool Registry Implementation (Infrastructure Layer).
"""
import logging
from typing import Any
from app.core.protocols import ToolRegistryProtocol, AgentTool
from app.services.agent_tools.domain.tool import StandardTool

logger = logging.getLogger(__name__)

class InMemoryToolRegistry:
    """
    Thread-safe in-memory registry for tools.
    """
    def __init__(self):
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is being overwritten.")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get(self, name: str) -> AgentTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[AgentTool]:
        return list(self._tools.values())

# Global Instance
global_registry = InMemoryToolRegistry()

def get_registry() -> ToolRegistryProtocol:
    return global_registry
