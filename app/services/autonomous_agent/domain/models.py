"""
Domain Models for the Autonomous Agent.
---------------------------------------
Defines the "Unit of Work" contract and the internal State Machine structure.
"""

from enum import StrEnum
from typing import Annotated, NotRequired, TypedDict, Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


def add_messages_reducer(
    left: list[BaseMessage], right: list[BaseMessage] | BaseMessage
) -> list[BaseMessage]:
    """Reducer to append messages to the history."""
    if isinstance(right, list):
        return [*left, *right]
    return [*left, right]


class AgentStatus(StrEnum):
    """The status of the Unit of Work."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


class UnitOfWork(BaseModel):
    """
    The Input Contract.
    Represents a discrete task assigned to the Autonomous Agent.
    """
    goal: str = Field(..., description="The primary objective of this unit of work.")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context or constraints.")
    max_retries: int = Field(default=3, description="Maximum number of self-correction loops.")


class WorkResult(BaseModel):
    """
    The Output Contract.
    Represents the final deliverable of the agent.
    """
    status: AgentStatus
    outcome: str = Field(..., description="The final answer or summary of work done.")
    artifacts: dict[str, Any] = Field(default_factory=dict, description="Structured data or file references generated.")
    quality_score: float = Field(0.0, description="The final quality score assigned by the Reflector.")


class PlanStep(BaseModel):
    """A single step in the execution plan."""
    id: int
    description: str
    tool: str | None = None
    status: str = "pending"  # pending, completed, failed


class AutonomousAgentState(TypedDict):
    """
    The Internal Graph State.
    Manages the lifecycle of the Unit of Work.
    """
    # Messaging
    messages: Annotated[list[BaseMessage], add_messages_reducer]

    # Core Data
    goal: str
    context: dict[str, Any]

    # Planning & Execution
    plan: list[PlanStep]
    current_step_index: int

    # Results accumulator
    results: dict[str, Any]  # Stores results from each step

    # Reflection & Control
    latest_critique: NotRequired[str]
    quality_score: NotRequired[float]
    retry_count: int
    status: AgentStatus

    # Output
    final_result: NotRequired[WorkResult]
