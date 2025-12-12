# app/services/governance/application/protocol_manager.py
"""
Protocol Manager Service
=========================
Single Responsibility: Manage existential protocols.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.services.governance.domain.models import PolicyStatus as CosmicPolicyStatus, ExistentialProtocol


class ProtocolRepository(Protocol):
    def save(self, protocol: ExistentialProtocol) -> ExistentialProtocol: ...
    def get(self, protocol_id: int) -> ExistentialProtocol | None: ...
    def update(self, protocol: ExistentialProtocol) -> None: ...


class TransparencyLogger(Protocol):
    def log_event(self, event_type: str, subject: str, details: dict, reasoning: str, impact: dict) -> None: ...


class ProtocolManager:
    """
    Existential protocol manager.
    
    Responsibilities:
    - Create protocols
    - Activate protocols
    - Check compliance
    """
    
    def __init__(
        self,
        protocol_repository: ProtocolRepository,
        transparency_logger: TransparencyLogger,
    ):
        self._protocol_repo = protocol_repository
        self._transparency = transparency_logger
    
    def create_protocol(
        self,
        protocol_name: str,
        description: str,
        cosmic_rules: dict[str, Any],
        version: str = "1.0.0",
    ) -> ExistentialProtocol:
        """Create new existential protocol"""
        protocol = ExistentialProtocol(
            protocol_name=protocol_name,
            protocol_version=version,
            description=description,
            cosmic_rules=cosmic_rules,
            status=CosmicPolicyStatus.PROPOSED,
            metadata_json={
                "created_by": "protocol_manager",
                "creation_method": "standard",
            },
        )
        
        saved_protocol = self._protocol_repo.save(protocol)
        
        # Log transparency event
        self._transparency.log_event(
            event_type="PROTOCOL_CREATED",
            subject=f"New Protocol: {protocol_name}",
            details={
                "protocol_id": saved_protocol.id,
                "protocol_name": protocol_name,
                "version": version,
                "status": CosmicPolicyStatus.PROPOSED.value,
            },
            reasoning=f"Protocol created to govern: {description}",
            impact={"new_protocol": True, "governance_expanded": True},
        )
        
        return saved_protocol
    
    def activate_protocol(self, protocol: ExistentialProtocol) -> bool:
        """Activate existential protocol"""
        try:
            protocol.status = CosmicPolicyStatus.ACTIVE
            protocol.activated_at = datetime.utcnow()
            self._protocol_repo.update(protocol)
            
            self._transparency.log_event(
                event_type="PROTOCOL_ACTIVATED",
                subject=f"Protocol Activated: {protocol.protocol_name}",
                details={"protocol_id": protocol.id},
                reasoning="Protocol ready for adoption",
                impact={"protocol_active": True},
            )
            
            return True
        except Exception:
            return False
    
    def check_protocol_compliance(
        self,
        protocol: ExistentialProtocol,
        consciousness_data: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Check if consciousness complies with protocol"""
        violations = []
        
        for rule_name, rule_spec in protocol.cosmic_rules.items():
            if not self._check_rule(rule_name, rule_spec, consciousness_data):
                violations.append(f"Violation: {rule_name}")
        
        is_compliant = len(violations) == 0
        return is_compliant, violations
    
    def _check_rule(
        self,
        rule_name: str,
        rule_spec: Any,
        consciousness_data: dict[str, Any],
    ) -> bool:
        """Check individual rule compliance"""
        # Simplified rule checking
        if isinstance(rule_spec, dict) and "required" in rule_spec:
            field = rule_spec.get("field")
            if field and field not in consciousness_data:
                return False
        
        return True
