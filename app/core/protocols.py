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

@runtime_checkable
class CollaborationContext(Protocol):
    """
    Protocol for shared state between agents.
    Provides a thread-safe (or loop-safe) mechanism to store and retrieve context.
    """
    shared_memory: dict[str, Any]

    def update(self, key: str, value: Any) -> None:
        """Updates a value in the shared memory."""
        ...

    def get(self, key: str) -> Any | None:
        """Retrieves a value from shared memory."""
        ...

@runtime_checkable
class AgentPlanner(Protocol):
    """Protocol for the Strategist Agent (Planning)."""
    async def create_plan(self, objective: str, context: CollaborationContext) -> dict[str, Any]:
        """Creates a strategic plan based on the objective."""
        ...

@runtime_checkable
class AgentArchitect(Protocol):
    """Protocol for the Architect Agent (Design)."""
    async def design_solution(self, plan: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """Creates a technical design/spec based on the plan."""
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """Protocol for the Operator Agent (Execution)."""
    async def execute_tasks(self, design: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """Executes the tasks defined in the design."""
        ...

@runtime_checkable
class AgentReflector(Protocol):
    """Protocol for the Auditor Agent (Review/Critique)."""
    async def review_work(
        self,
        result: dict[str, Any],
        original_objective: str,
        context: CollaborationContext
    ) -> dict[str, Any]:
        """Reviews the execution result against the objective."""
        ...
