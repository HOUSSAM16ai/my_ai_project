# app/services/governance/application/council_manager.py
"""
Council Manager Service
========================
Single Responsibility: Manage cosmic governance councils.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Protocol

from app.models import CosmicGovernanceCouncil


class CouncilRepository(Protocol):
    def save(self, council: CosmicGovernanceCouncil) -> CosmicGovernanceCouncil: ...
    def get(self, council_id: int) -> CosmicGovernanceCouncil | None: ...
    def update(self, council: CosmicGovernanceCouncil) -> None: ...


class TransparencyLogger(Protocol):
    def log_event(self, event_type: str, subject: str, details: dict, reasoning: str, impact: dict) -> None: ...


class CouncilManager:
    """
    Cosmic governance council manager.
    
    Responsibilities:
    - Create councils
    - Add members
    - Manage decisions
    - Voting and consensus
    """
    
    MIN_COUNCIL_MEMBERS = 3
    CONSENSUS_THRESHOLD = 0.75
    
    def __init__(
        self,
        council_repository: CouncilRepository,
        transparency_logger: TransparencyLogger,
    ):
        self._council_repo = council_repository
        self._transparency = transparency_logger
    
    def create_council(
        self,
        council_name: str,
        purpose: str,
        consensus_threshold: float = 0.75,
    ) -> CosmicGovernanceCouncil:
        """Create new cosmic council"""
        council = CosmicGovernanceCouncil(
            council_name=council_name,
            purpose=purpose,
            consensus_threshold=consensus_threshold,
            members=[], 
            pending_decisions={},
            decision_history=[],
        )
        
        saved_council = self._council_repo.save(council)
        
        self._transparency.log_event(
            event_type="COUNCIL_CREATED",
            subject=f"New Council: {council_name}",
            details={"council_id": saved_council.id, "purpose": purpose},
            reasoning="Council created for governance",
            impact={"new_council": True},
        )
        
        return saved_council
    
    def add_member(
        self,
        council: CosmicGovernanceCouncil,
        consciousness_signature: str,
    ) -> bool:
        """Add member to council"""
        if consciousness_signature not in council.members:
            council.members.append(consciousness_signature)
            self._council_repo.update(council)
            
            self._transparency.log_event(
                event_type="COUNCIL_MEMBER_ADDED",
                subject=f"Member Added to {council.council_name}",
                details={"council_id": council.id, "member": consciousness_signature},
                reasoning="Expanding council membership",
                impact={"member_added": True},
            )
            
            return True
        return False
    
    def propose_decision(
        self,
        council: CosmicGovernanceCouncil,
        proposal: str,
        proposed_by: str,
    ) -> str:
        """Propose new decision"""
        decision_id = hashlib.sha256(
            f"{council.id}{proposal}{datetime.utcnow()}".encode()
        ).hexdigest()[:16]
        
        council.pending_decisions[decision_id] = {
            "proposal": proposal,
            "proposed_by": proposed_by,
            "votes_for": [],
            "votes_against": [],
            "votes_abstain": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._council_repo.update(council)
        
        self._transparency.log_event(
            event_type="DECISION_PROPOSED",
            subject=f"Decision Proposed: {proposal}",
            details={"council_id": council.id, "decision_id": decision_id},
            reasoning="New proposal for council consideration",
            impact={"proposal_created": True},
        )
        
        return decision_id
    
    def vote_on_decision(
        self,
        council: CosmicGovernanceCouncil,
        decision_id: str,
        voter_signature: str,
        vote: str,  # "for", "against", "abstain"
    ) -> bool:
        """Record vote on decision"""
        if decision_id not in council.pending_decisions:
            return False
        
        decision = council.pending_decisions[decision_id]
        
        # Remove from all vote lists first
        for vote_list in ["votes_for", "votes_against", "votes_abstain"]:
            if voter_signature in decision[vote_list]:
                decision[vote_list].remove(voter_signature)
        
        # Add to appropriate list
        if vote == "for":
            decision["votes_for"].append(voter_signature)
        elif vote == "against":
            decision["votes_against"].append(voter_signature)
        elif vote == "abstain":
            decision["votes_abstain"].append(voter_signature)
        
        self._council_repo.update(council)
        return True
    
    def check_consensus_reached(
        self,
        council: CosmicGovernanceCouncil,
        decision_id: str,
    ) -> tuple[bool, str]:
        """Check if consensus reached on decision"""
        if decision_id not in council.pending_decisions:
            return False, "pending"
        
        decision = council.pending_decisions[decision_id]
        total_votes = len(decision["votes_for"]) + len(decision["votes_against"])
        
        if total_votes == 0:
            return False, "pending"
        
        approval_rate = len(decision["votes_for"]) / total_votes
        
        if approval_rate >= council.consensus_threshold:
            return True, "approved"
        elif approval_rate < (1 - council.consensus_threshold):
            return True, "rejected"
        else:
            return False, "pending"
    
    def get_council_analytics(
        self,
        council: CosmicGovernanceCouncil,
    ) -> dict[str, Any]:
        """Get council analytics"""
        return {
            "council_id": council.id,
            "council_name": council.council_name,
            "total_members": len(council.members),
            "pending_decisions": len(council.pending_decisions),
            "total_decisions": len(council.decision_history),
            "consensus_threshold": council.consensus_threshold,
        }
