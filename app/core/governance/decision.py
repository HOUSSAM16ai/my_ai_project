"""
Decision Kernel & Sovereignty.
------------------------------
This module defines the "Brain" of the architecture.
It centralizes the concept of a "Decision" to prevent Orchestration Drift.

Key Concepts:
- DecisionRecord: The immutable artifact of a choice.
- Policy: The logic that produces a Decision.
- Intent: The input triggering a decision.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, List, Optional, TypeVar

from pydantic import Field

from app.core.governance.contracts import GovernanceModel
from app.core.governance.errors import FailureClass

# Generic Input Type (The Context)
I = TypeVar("I", bound=GovernanceModel)
# Generic Output Type (The Action/Result)
O = TypeVar("O", bound=GovernanceModel)


class DecisionIntent(GovernanceModel):
    """
    Represents the "Why" - the trigger for a decision.
    """

    intent_key: str = Field(..., description="Unique key for this intent type")
    source: str = Field(..., description="Who requested this?")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionRecord(GovernanceModel, Generic[O]):
    """
    The Immutable Artifact of a Decision.
    Traceable proof of why the system did what it did.
    """

    decision_id: str = Field(..., description="Unique ID for this specific decision instance")
    policy_name: str = Field(..., description="Name of the policy that made this decision")
    status: str = Field(..., description="Outcome status (e.g. SUCCESS, FAILED)")
    failure_class: Optional[FailureClass] = Field(
        None, description="Taxonomy of failure if applicable"
    )
    result: Optional[O] = Field(None, description="The resulting action/value")
    reasoning: str = Field(..., description="Human-readable explanation of the choice")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Policy(ABC, Generic[I, O]):
    """
    Abstract Base Class for all Decision Policies.
    A Policy is a pure function (conceptually) that maps Context -> Decision.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this policy."""
        pass

    @abstractmethod
    def evaluate(self, context: I) -> DecisionRecord[O]:
        """
        Execute the policy logic.
        MUST NOT raise naked exceptions.
        MUST return a DecisionRecord with failure_class if things go wrong.
        """
        pass
