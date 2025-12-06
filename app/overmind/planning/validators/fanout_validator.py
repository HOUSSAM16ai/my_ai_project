# app/overmind/planning/validators/fanout_validator.py
"""
Fan-out validator for plan validation.

Validates maximum fan-out (out-degree) of tasks.
Complexity: CC ≤ 3
"""

from typing import Any

from .graph_builder import GraphData


class FanoutValidator:
    """Validates maximum fan-out of tasks."""

    def __init__(self, settings: Any):
        self.settings = settings

    def validate(self, graph_data: GraphData) -> list[Any]:
        """
        Validate fan-out constraints.

        Complexity: CC=3
        """
        from ..schemas import PlanValidationIssue

        issues = []

        for parent, children in graph_data.adjacency.items():
            if len(children) > self.settings.MAX_OUT_DEGREE:
                issues.append(
                    PlanValidationIssue(
                        code="EXCESS_OUT_DEGREE",
                        message=f"Task '{parent}' fan-out {len(children)} > MAX_OUT_DEGREE={self.settings.MAX_OUT_DEGREE}",
                        task_id=parent,
                    )
                )

        return issues
