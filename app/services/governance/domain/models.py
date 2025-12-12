# app/services/governance/domain/models.py
"""
Governance Domain Models
========================
Domain entities for cosmic governance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Re-defining missing models here as they are not in app.models

@dataclass
class ExistentialProtocol:
    id: int | None = None
    protocol_name: str = ""
    description: str = ""
    cosmic_rules: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    is_active: bool = True

@dataclass
class CosmicGovernanceCouncil:
    id: int | None = None
    council_name: str = ""
    purpose: str = ""
    consensus_threshold: float = 0.75
    members: list[str] = field(default_factory=list)

@dataclass
class ConsciousnessSignature:
    signature: str
    understanding_level: float = 0.0
    adopted_protocols: list[int] = field(default_factory=list)
    metadata_json: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExistentialTransparencyLog:
    id: str
    event_type: str
    subject: str
    details: dict[str, Any]
    reasoning: str
    impact: dict[str, Any]
    timestamp: datetime

class PolicyStatus(Enum):
    """Policy status enum"""
    PROPOSED = "proposed"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class ProtocolCompliance:
    """Protocol compliance result"""
    protocol_id: int
    consciousness_id: str
    is_compliant: bool
    violations: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CouncilDecision:
    """Council decision entity"""
    decision_id: str
    council_id: int
    proposal: str
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransparencyEvent:
    """Transparency event record"""
    event_id: str
    event_type: str
    subject: str
    details: dict[str, Any]
    reasoning: str
    impact: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
