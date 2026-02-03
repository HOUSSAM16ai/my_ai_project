"""
Multi-Agent Fabric Specification (MAF-1.0) Models.
--------------------------------------------------
This module defines the normative data structures for the High-Reliability Agent System.
Adheres to the "Evidence-Based Output" doctrine.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditStatus(str, Enum):
    """
    Status of a verification or audit process.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class MAFPhase(str, Enum):
    """
    The distinct phases of the MAF Protocol.
    """

    GENERATE = "GENERATE"  # Production of Claims/Proposals
    ATTACK = "ATTACK"  # Adversarial testing / Critique
    VERIFY = "VERIFY"  # Formal verification against evidence
    SEAL = "SEAL"  # Finalization and Audit Bundling


class Evidence(BaseModel):
    """
    A verifiable piece of information supporting a Claim.
    """

    id: str = Field(..., description="Unique identifier for the evidence")
    content: str = Field(..., description="The evidence content (quote, result, axiom)")
    source_type: str = Field(..., description="Type: 'document', 'simulation', 'logic', 'axiom'")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Claim(BaseModel):
    """
    A partial result or assertion that requires evidence.
    """

    id: str = Field(..., description="Unique identifier for the claim")
    content: str = Field(..., description="The assertion text")
    evidence_ids: list[str] = Field(default_factory=list, description="IDs of supporting evidence")


class Proposal(BaseModel):
    """
    An agent's proposed solution, containing claims and estimates.
    """

    claims: list[Claim] = Field(default_factory=list)
    cost_est: float = Field(0.0, description="Estimated computational cost")
    risk_est: float = Field(0.0, description="Estimated risk score")
    time_est: float = Field(0.0, description="Estimated latency")
    raw_content: str = Field(..., description="The original text content of the proposal")


class AttackReport(BaseModel):
    """
    Result of an adversarial attack on a Proposal.
    """

    counterexamples: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    severity: float = Field(0.0, description="Severity of the attack 0.0-10.0")
    successful: bool = Field(..., description="True if the attack found significant flaws")
    feedback: str = Field(..., description="Constructive feedback for regeneration")


class Verification(BaseModel):
    """
    Result of the formal verification process.
    """

    passed: bool = Field(..., description="True if all Critical Gates passed")
    status: AuditStatus = Field(default=AuditStatus.SKIPPED)
    evidence_ids: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    risk_score: float = Field(0.0, description="Residual risk score")


class AuditBundle(BaseModel):
    """
    The 'Sealed' final output, containing the entire provenance chain.
    """

    task_id: str
    claims: list[Claim]
    evidence: list[Evidence]
    verification: Verification
    attack_report: AttackReport | None = None
    decision_reason: str
    final_text: str
