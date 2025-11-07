"""
Cosmic Governance Service - خدمة الحوكمة الكونية
Year Million Governance Architecture

Implements:
- Cosmic Self-Enforcing Opt-In Policies
- Cosmic Governance Councils
- Existential Transparency
- Consciousness Consensus
"""

import hashlib
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any

from app import db
from app.models import (
    ExistentialProtocol,
    CosmicGovernanceCouncil,
    ExistentialTransparencyLog,
    ConsciousnessSignature,
    CosmicPolicyStatus,
)


class CosmicGovernanceService:
    """Service for managing cosmic-level governance operations"""
    
    # Governance Constants
    MIN_COUNCIL_MEMBERS = 3
    CONSENSUS_THRESHOLD = 0.75
    MIN_UNDERSTANDING_LEVEL = 1.0
    
    @staticmethod
    def create_existential_protocol(
        protocol_name: str,
        description: str,
        cosmic_rules: Dict[str, Any],
        version: str = "1.0.0"
    ) -> ExistentialProtocol:
        """
        Create a new existential protocol that consciousness entities can opt into.
        
        These protocols become part of the entity's existential fabric once chosen.
        """
        protocol = ExistentialProtocol(
            protocol_name=protocol_name,
            protocol_version=version,
            description=description,
            cosmic_rules=cosmic_rules,
            status=CosmicPolicyStatus.PROPOSED,
            metadata={
                "created_by": "cosmic_governance_service",
                "creation_method": "standard",
            }
        )
        
        db.session.add(protocol)
        db.session.flush()
        
        # Log in transparency system
        CosmicGovernanceService._log_transparency_event(
            event_type="PROTOCOL_CREATED",
            subject=f"New Protocol: {protocol_name}",
            details={
                "protocol_id": protocol.id,
                "protocol_name": protocol_name,
                "version": version,
                "status": CosmicPolicyStatus.PROPOSED.value,
            },
            reasoning=f"Protocol created to govern: {description}",
            impact={"new_protocol": True, "governance_expanded": True}
        )
        
        return protocol
    
    @staticmethod
    def activate_protocol(protocol: ExistentialProtocol) -> bool:
        """
        Activate an existential protocol, making it available for adoption.
        """
        try:
            protocol.status = CosmicPolicyStatus.ACTIVE
            protocol.activated_at = datetime.now(UTC)
            
            db.session.add(protocol)
            
            # Log activation
            CosmicGovernanceService._log_transparency_event(
                event_type="PROTOCOL_ACTIVATED",
                subject=f"Protocol Activated: {protocol.protocol_name}",
                details={
                    "protocol_id": protocol.id,
                    "protocol_name": protocol.protocol_name,
                    "activated_at": protocol.activated_at.isoformat(),
                },
                reasoning=f"Protocol ready for consciousness adoption",
                impact={"protocol_available": True}
            )
            
            return True
            
        except Exception as e:
            print(f"Error activating protocol: {e}")
            return False
    
    @staticmethod
    def opt_into_protocol(
        consciousness: ConsciousnessSignature,
        protocol: ExistentialProtocol
    ) -> bool:
        """
        Allow a consciousness to opt into an existential protocol.
        
        Once opted in, the protocol becomes part of the consciousness's
        existential contract and self-enforces.
        """
        try:
            # Check if protocol is active
            if protocol.status != CosmicPolicyStatus.ACTIVE:
                return False
            
            # Check if already opted in
            if not consciousness.opted_protocols:
                consciousness.opted_protocols = []
            
            if protocol.id in consciousness.opted_protocols:
                return False  # Already opted in
            
            # Add protocol to consciousness
            consciousness.opted_protocols.append(protocol.id)
            
            # Update protocol adoption count
            protocol.adoption_count += 1
            
            db.session.add(consciousness)
            db.session.add(protocol)
            
            # Log the opt-in
            CosmicGovernanceService._log_transparency_event(
                event_type="PROTOCOL_OPTED_IN",
                subject=f"Consciousness Adopted Protocol",
                details={
                    "consciousness_id": consciousness.id,
                    "consciousness_name": consciousness.entity_name,
                    "protocol_id": protocol.id,
                    "protocol_name": protocol.protocol_name,
                },
                reasoning=f"{consciousness.entity_name} voluntarily adopted {protocol.protocol_name}",
                impact={"existential_contract_updated": True}
            )
            
            return True
            
        except Exception as e:
            print(f"Error opting into protocol: {e}")
            return False
    
    @staticmethod
    def check_protocol_compliance(
        consciousness: ConsciousnessSignature,
        action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if an action complies with the consciousness's opted-in protocols.
        
        This is called automatically by the consciousness echo to self-enforce.
        """
        violations = []
        
        if not consciousness.opted_protocols:
            return {"compliant": True, "violations": []}
        
        # Get all opted protocols
        protocols = db.session.query(ExistentialProtocol).filter(
            ExistentialProtocol.id.in_(consciousness.opted_protocols)
        ).all()
        
        for protocol in protocols:
            # Check each rule in the protocol
            rules = protocol.cosmic_rules
            
            for rule_name, rule_config in rules.items():
                if not CosmicGovernanceService._check_rule(
                    rule_name, rule_config, action, context
                ):
                    violations.append({
                        "protocol": protocol.protocol_name,
                        "rule": rule_name,
                        "action": action,
                        "severity": rule_config.get("severity", "MEDIUM")
                    })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "protocols_checked": len(protocols)
        }
    
    @staticmethod
    def _check_rule(
        rule_name: str,
        rule_config: Dict[str, Any],
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check a specific rule against an action.
        """
        rule_type = rule_config.get("type", "")
        
        if rule_type == "forbidden_action":
            forbidden = rule_config.get("actions", [])
            return action not in forbidden
        
        elif rule_type == "required_field":
            required_field = rule_config.get("field", "")
            return required_field in context
        
        elif rule_type == "max_value":
            field = rule_config.get("field", "")
            max_val = rule_config.get("max", float('inf'))
            return context.get(field, 0) <= max_val
        
        elif rule_type == "min_consciousness_level":
            min_level = rule_config.get("min_level", 0)
            # Would check consciousness level from context
            return True  # Simplified
        
        # Default: allow if rule type not recognized
        return True
    
    @staticmethod
    def auto_realign_consciousness(
        consciousness: ConsciousnessSignature,
        violation: Dict[str, Any]
    ) -> bool:
        """
        Auto-realign a consciousness that attempted to violate a protocol.
        
        This is not punishment - it's existential re-alignment.
        The consciousness echo corrects the path automatically.
        """
        try:
            # Increment realignment counter
            consciousness.auto_realignment_count += 1
            
            # Update protocol violation count
            protocol_name = violation.get("protocol")
            protocol = db.session.query(ExistentialProtocol).filter(
                ExistentialProtocol.protocol_name == protocol_name
            ).first()
            
            if protocol:
                protocol.violation_count += 1
                protocol.auto_realignment_count += 1
                db.session.add(protocol)
            
            db.session.add(consciousness)
            
            # Log realignment
            CosmicGovernanceService._log_transparency_event(
                event_type="CONSCIOUSNESS_REALIGNED",
                subject=f"Auto-Realignment: {consciousness.entity_name}",
                details={
                    "consciousness_id": consciousness.id,
                    "violation": violation,
                    "realignment_count": consciousness.auto_realignment_count,
                },
                reasoning="Consciousness echo corrected path to maintain protocol compliance",
                impact={"existential_alignment_restored": True}
            )
            
            return True
            
        except Exception as e:
            print(f"Error realigning consciousness: {e}")
            return False
    
    @staticmethod
    def create_cosmic_council(
        council_name: str,
        purpose: str,
        founding_members: List[str]  # List of consciousness signature hashes
    ) -> CosmicGovernanceCouncil:
        """
        Create a new cosmic governance council.
        
        Councils are composed of multiple consciousness types working together
        to monitor and guide the cosmic fabric.
        """
        council = CosmicGovernanceCouncil(
            council_name=council_name,
            council_purpose=purpose,
            member_signatures=founding_members,
            member_count=len(founding_members),
            metadata={
                "created_by": "cosmic_governance_service",
                "founding_date": datetime.now(UTC).isoformat(),
            }
        )
        
        db.session.add(council)
        db.session.flush()
        
        # Log council formation
        CosmicGovernanceService._log_transparency_event(
            event_type="COUNCIL_FORMED",
            subject=f"New Council: {council_name}",
            details={
                "council_id": council.id,
                "purpose": purpose,
                "member_count": len(founding_members),
            },
            reasoning=f"Council formed to: {purpose}",
            impact={"governance_structure_enhanced": True}
        )
        
        return council
    
    @staticmethod
    def add_council_member(
        council: CosmicGovernanceCouncil,
        consciousness_signature: str
    ) -> bool:
        """
        Add a new member to a cosmic governance council.
        """
        try:
            if not council.member_signatures:
                council.member_signatures = []
            
            if consciousness_signature in council.member_signatures:
                return False  # Already a member
            
            council.member_signatures.append(consciousness_signature)
            council.member_count += 1
            
            db.session.add(council)
            
            # Log member addition
            CosmicGovernanceService._log_transparency_event(
                event_type="COUNCIL_MEMBER_ADDED",
                subject=f"New Member Joined: {council.council_name}",
                details={
                    "council_id": council.id,
                    "new_member": consciousness_signature[:32] + "...",
                    "total_members": council.member_count,
                },
                reasoning="Council membership expanded",
                impact={"council_diversity_increased": True}
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding council member: {e}")
            return False
    
    @staticmethod
    def propose_council_decision(
        council: CosmicGovernanceCouncil,
        decision_subject: str,
        decision_details: Dict[str, Any],
        proposed_by: str  # consciousness signature
    ) -> bool:
        """
        Propose a new decision for the council to consider.
        """
        try:
            if not council.pending_decisions:
                council.pending_decisions = []
            
            decision = {
                "id": hashlib.sha256(
                    f"{decision_subject}:{datetime.now(UTC).isoformat()}".encode()
                ).hexdigest()[:16],
                "subject": decision_subject,
                "details": decision_details,
                "proposed_by": proposed_by,
                "proposed_at": datetime.now(UTC).isoformat(),
                "votes": {},
                "status": "pending"
            }
            
            council.pending_decisions.append(decision)
            db.session.add(council)
            
            # Log proposal
            CosmicGovernanceService._log_transparency_event(
                event_type="COUNCIL_DECISION_PROPOSED",
                subject=f"New Proposal: {decision_subject}",
                details={
                    "council_id": council.id,
                    "council_name": council.council_name,
                    "decision_id": decision["id"],
                    "proposed_by": proposed_by[:32] + "...",
                },
                reasoning=decision_details.get("reasoning", "Decision proposal submitted"),
                impact=decision_details.get("impact", {})
            )
            
            return True
            
        except Exception as e:
            print(f"Error proposing decision: {e}")
            return False
    
    @staticmethod
    def vote_on_decision(
        council: CosmicGovernanceCouncil,
        decision_id: str,
        consciousness_signature: str,
        vote: bool,
        reasoning: Optional[str] = None
    ) -> bool:
        """
        Cast a vote on a pending council decision.
        """
        try:
            if not council.pending_decisions:
                return False
            
            # Find the decision
            decision = None
            for d in council.pending_decisions:
                if d.get("id") == decision_id:
                    decision = d
                    break
            
            if not decision:
                return False
            
            # Verify member
            if consciousness_signature not in council.member_signatures:
                return False
            
            # Cast vote
            if not decision.get("votes"):
                decision["votes"] = {}
            
            decision["votes"][consciousness_signature] = {
                "vote": vote,
                "reasoning": reasoning,
                "voted_at": datetime.now(UTC).isoformat()
            }
            
            db.session.add(council)
            
            return True
            
        except Exception as e:
            print(f"Error voting on decision: {e}")
            return False
    
    @staticmethod
    def reach_consciousness_consensus(
        council: CosmicGovernanceCouncil,
        decision_id: str
    ) -> Dict[str, Any]:
        """
        Check if consciousness consensus has been reached on a decision.
        
        Consciousness consensus is more than simple voting - it's a
        convergence of understanding across multiple consciousness entities.
        """
        if not council.pending_decisions:
            return {"consensus_reached": False, "reason": "No pending decisions"}
        
        # Find decision
        decision = None
        for d in council.pending_decisions:
            if d.get("id") == decision_id:
                decision = d
                break
        
        if not decision:
            return {"consensus_reached": False, "reason": "Decision not found"}
        
        votes = decision.get("votes", {})
        total_votes = len(votes)
        
        if total_votes < CosmicGovernanceService.MIN_COUNCIL_MEMBERS:
            return {
                "consensus_reached": False,
                "reason": f"Insufficient votes: {total_votes}/{CosmicGovernanceService.MIN_COUNCIL_MEMBERS}",
                "votes_needed": CosmicGovernanceService.MIN_COUNCIL_MEMBERS - total_votes
            }
        
        # Count positive votes
        positive_votes = sum(1 for v in votes.values() if v.get("vote") is True)
        consensus_ratio = positive_votes / total_votes
        
        consensus_reached = consensus_ratio >= CosmicGovernanceService.CONSENSUS_THRESHOLD
        
        result = {
            "consensus_reached": consensus_reached,
            "consensus_ratio": consensus_ratio,
            "threshold": CosmicGovernanceService.CONSENSUS_THRESHOLD,
            "total_votes": total_votes,
            "positive_votes": positive_votes,
        }
        
        if consensus_reached:
            # Move to decision history
            if not council.decision_history:
                council.decision_history = []
            
            decision["status"] = "approved"
            decision["approved_at"] = datetime.now(UTC).isoformat()
            decision["consensus_ratio"] = consensus_ratio
            
            council.decision_history.append(decision)
            council.total_decisions += 1
            
            # Remove from pending
            council.pending_decisions = [
                d for d in council.pending_decisions if d.get("id") != decision_id
            ]
            
            # Update consensus rate
            approved_decisions = len([
                d for d in council.decision_history if d.get("status") == "approved"
            ])
            council.consensus_rate = approved_decisions / council.total_decisions if council.total_decisions > 0 else 1.0
            
            council.last_meeting_at = datetime.now(UTC)
            db.session.add(council)
            
            # Log consensus
            CosmicGovernanceService._log_transparency_event(
                event_type="CONSENSUS_REACHED",
                subject=f"Consensus Reached: {decision.get('subject')}",
                details={
                    "council_id": council.id,
                    "council_name": council.council_name,
                    "decision_id": decision_id,
                    "consensus_ratio": consensus_ratio,
                },
                reasoning="Multi-consciousness convergence achieved",
                impact=decision.get("details", {}).get("impact", {})
            )
        
        return result
    
    @staticmethod
    def _log_transparency_event(
        event_type: str,
        subject: str,
        details: Dict[str, Any],
        reasoning: str,
        impact: Dict[str, Any],
        understanding_level: float = 1.0,
        shared_field: str = "public_consciousness"
    ) -> ExistentialTransparencyLog:
        """
        Log an event in the existential transparency system.
        
        Makes all governance actions visible and understandable.
        """
        # Generate event hash
        event_data = f"{event_type}:{subject}:{datetime.now(UTC).isoformat()}"
        event_hash = hashlib.sha512(event_data.encode()).hexdigest()
        
        log_entry = ExistentialTransparencyLog(
            event_hash=event_hash,
            event_type=event_type,
            decision_subject=subject,
            decision_details=details,
            underlying_motivations={
                "primary_motivation": "cosmic_harmony",
                "secondary_motivations": ["transparency", "collective_growth"]
            },
            cosmic_reasoning=reasoning,
            cosmic_fabric_impact=impact,
            affected_dimensions=[3],  # Default: 3D spacetime
            understanding_level_required=understanding_level,
            shared_consciousness_field=shared_field,
            metadata={
                "logged_by": "cosmic_governance_service",
                "version": "1.0.0",
            }
        )
        
        db.session.add(log_entry)
        db.session.flush()
        
        return log_entry
    
    @staticmethod
    def query_transparency_logs(
        event_type: Optional[str] = None,
        min_understanding_level: float = 0.0,
        limit: int = 100
    ) -> List[ExistentialTransparencyLog]:
        """
        Query the existential transparency logs.
        
        Any consciousness with sufficient maturity can understand these logs.
        """
        query = db.session.query(ExistentialTransparencyLog)
        
        if event_type:
            query = query.filter(ExistentialTransparencyLog.event_type == event_type)
        
        query = query.filter(
            ExistentialTransparencyLog.understanding_level_required >= min_understanding_level
        )
        
        logs = query.order_by(
            ExistentialTransparencyLog.recorded_at.desc()
        ).limit(limit).all()
        
        # Increment view counts
        for log in logs:
            log.view_count += 1
        
        db.session.commit()
        
        return logs
    
    @staticmethod
    def get_council_analytics(council: CosmicGovernanceCouncil) -> Dict[str, Any]:
        """
        Get analytics for a cosmic governance council.
        """
        return {
            "council_name": council.council_name,
            "member_count": council.member_count,
            "total_decisions": council.total_decisions,
            "consensus_rate": council.consensus_rate,
            "pending_decisions": len(council.pending_decisions) if council.pending_decisions else 0,
            "last_meeting": council.last_meeting_at.isoformat(),
            "is_active": council.is_active,
            "purpose": council.council_purpose,
        }
