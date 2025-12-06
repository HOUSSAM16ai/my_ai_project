from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from ...schemas import PlannedTask

@runtime_checkable
class PlanningStep(Protocol):
    """Protocol for an atomic planning step."""

    def execute(
        self,
        tasks: list[PlannedTask],
        idx: int,
        context: dict[str, Any],
    ) -> int:
        """
        Execute the planning step.

        Args:
            tasks: The list of planned tasks to append to.
            idx: The current task index counter.
            context: Shared context dictionary (read/write).

        Returns:
            The updated task index counter.
        """
        ...
