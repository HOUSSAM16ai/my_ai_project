"""
Core Protocols & Interfaces
Defines abstract base classes and protocols for the application.
"""
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseService(Protocol):
    """Base protocol for all application services."""
    pass

@runtime_checkable
class RepositoryProtocol(Protocol):
    """Base protocol for repositories."""
    pass

# ======================================================================================
# AI Agent Protocols (SOLID: ISP & DIP)
# ======================================================================================

@runtime_checkable
class AgentTool(Protocol):
    """
    Protocol for an autonomous agent tool.
    Each tool must have a single responsibility (SRP).
    """
    @property
    def name(self) -> str:
        """The unique name of the tool."""
        ...

    @property
    def description(self) -> str:
        """A description of what the tool does."""
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON schema for tool parameters."""
        ...

    async def execute(self, **kwargs) -> Any:
        """Executes the tool logic."""
        ...

@runtime_checkable
class ToolRegistryProtocol(Protocol):
    """
    Protocol for managing tools (OCP).
    Allows adding new tools without modifying the consumer.
    """
    def register(self, tool: AgentTool) -> None:
        """Registers a new tool."""
        ...

    def get(self, name: str) -> AgentTool | None:
        """Retrieves a tool by name."""
        ...

    def list_tools(self) -> list[AgentTool]:
        """Lists all available tools."""
        ...

@runtime_checkable
class AgentMemory(Protocol):
    """
    Protocol for Agent Memory.
    """
    async def store(self, key: str, value: Any) -> None:
        ...

    async def retrieve(self, key: str) -> Any:
        ...

@runtime_checkable
class AgentPlanner(Protocol):
    """
    Protocol for high-level planning.
    """
    async def create_plan(self, objective: str) -> dict[str, Any]:
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """
    Protocol for executing plans.
    """
    async def execute_plan(self, plan: dict[str, Any]) -> Any:
        ...
