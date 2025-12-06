# app/overmind/planning/validators/basic_validator.py
"""
Basic constraints validator.

Validates fundamental plan constraints like task count and emptiness.
Complexity: CC ≤ 4
"""

from typing import Any


class BasicConstraintsValidator:
    """Validates basic plan constraints."""
    
    def __init__(self, settings: Any):
        self.settings = settings
    
    def validate(self, plan: Any) -> list[Any]:
        """
        Validate basic constraints.
        
        Complexity: CC=4
        Returns: List of validation issues
        """
        from ..schemas import PlanValidationIssue
        
        issues = []
        
        if not plan.tasks:
            issues.append(
                PlanValidationIssue(
                    code="EMPTY_PLAN",
                    message="Plan has no tasks"
                )
            )
        
        if len(plan.tasks) > self.settings.MAX_TASKS:
            issues.append(
                PlanValidationIssue(
                    code="TOO_MANY_TASKS",
                    message=f"Task count {len(plan.tasks)} exceeds MAX_TASKS={self.settings.MAX_TASKS}"
                )
            )
        
        return issues
