"""Planner interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Any


class PlannerInterface(ABC):
    """Abstract interface for all planners."""

    @abstractmethod
    def generate_plan(
        self,
        objective: str,
        context: dict[str, Any] | None = None,
        max_tasks: int | None = None,
    ) -> dict[str, Any]:
        """Generate a plan for the given objective.

        Args:
            objective: The goal to achieve
            context: Additional context for planning
            max_tasks: Maximum number of tasks to generate

        Returns:
            Plan dictionary with tasks and metadata
        """

    @abstractmethod
    def validate_plan(self, plan: dict[str, Any]) -> bool:
        """Validate a generated plan.

        Args:
            plan: Plan to validate

        Returns:
            True if valid, False otherwise
        """

    @abstractmethod
    def get_capabilities(self) -> set[str]:
        """Get planner capabilities.

        Returns:
            Set of capability strings
        """
