# app/overmind/planning/validators/depth_validator.py
"""
Depth validator for plan validation.

Validates maximum depth of dependency graph.
Complexity: CC ≤ 3
"""

from typing import Any


class DepthValidator:
    """Validates maximum depth of dependency graph."""

    def __init__(self, settings: Any):
        self.settings = settings

    def validate(self, depth_map: dict[str, int]) -> list[Any]:
        """
        Validate depth constraints.

        Complexity: CC=3
        """
        from ..schemas import PlanValidationIssue

        issues = []

        if not depth_map:
            return issues

        longest_path = max(depth_map.values())

        if longest_path > self.settings.MAX_DEPTH:
            issues.append(
                PlanValidationIssue(
                    code="DEPTH_EXCEEDED",
                    message=f"Depth {longest_path} > MAX_DEPTH={self.settings.MAX_DEPTH}",
                )
            )

        return issues
