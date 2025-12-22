"""
Core Protocols & Interfaces
Defines abstract base classes and protocols for the application.
"""
from typing import Any, Protocol, runtime_checkable
from collections.abc import Awaitable

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

    def execute(self, **kwargs) -> Awaitable[Any]:
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
    def store(self, key: str, value: Any) -> Awaitable[None]:
        ...

    def retrieve(self, key: str) -> Awaitable[Any]:
        ...

@runtime_checkable
class AgentPlanner(Protocol):
    """
    Protocol for high-level planning.
    يحدد كيفية تحويل الهدف إلى خطة قابلة للتنفيذ.
    """
    def create_plan(self, objective: str) -> Awaitable[dict[str, Any]]:
        """
        Creates a plan based on the objective.
        Returns a JSON-compatible dictionary representing the plan.
        """
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """
    Protocol for executing plans.
    المسؤول عن تنفيذ المهام فعلياً.
    """
    def execute_task(self, task: Any) -> Awaitable[dict[str, Any]]:
        """
        Executes a single task.
        Returns a result dictionary.
        """
        ...

@runtime_checkable
class AgentReflector(Protocol):
    """
    Protocol for Self-Reflection (Critique).
    المسؤول عن نقد النتائج والخطط (التفكير الذاتي).
    """
    def critique_plan(self, objective: str, plan: dict[str, Any]) -> Awaitable[dict[str, Any]]:
        """
        Reviews a plan before execution.
        Returns a verdict (approved/rejected) and feedback.
        """
        ...

    def critique_result(self, task: Any, result: Any) -> Awaitable[dict[str, Any]]:
        """
        Reviews a task result.
        Returns a verdict and suggestions for improvement.
        """
        ...
