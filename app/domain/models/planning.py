"""
Planning Domain Models.
-----------------------
Defines the data structures for planning and curriculum generation.
These models act as an Anti-Corruption Layer (ACL) for the Planning Agent.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    """Payload for generating a new educational plan."""

    goal: str = Field(..., description="Main learning goal")
    context: list[str] = Field(default_factory=list, description="Additional context")


class PlanResult(BaseModel):
    """The generated plan result."""

    plan_id: UUID | None = None
    goal: str
    steps: list[str]
