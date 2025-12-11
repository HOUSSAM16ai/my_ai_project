# app/services/governance/domain/models.py
"""
Governance Domain Models
========================
Domain entities for cosmic governance (imported from app.models).
"""

# Domain models already exist in app.models, so we import them
# This maintains clean architecture by creating a domain layer reference

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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
