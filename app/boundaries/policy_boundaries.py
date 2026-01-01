"""
Policy Boundaries - حدود السياسات
==================================

Policy boundary pattern implementation for security and compliance.
تطبيق نمط حدود السياسات للأمن والامتثال.

Key Components:
- PolicyBoundary: Main policy boundary container
- PolicyEngine: Policy evaluation engine
- SecurityPipeline: Multi-layer security pipeline
- DataGovernance: Data governance and classification
- ComplianceEngine: Compliance validation
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Effect(Enum):
    """Policy effect - تأثير السياسة"""

    ALLOW = "allow"
    DENY = "deny"


class DataClassification(Enum):
    """Data classification levels - مستويات تصنيف البيانات"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_RESTRICTED = "highly_restricted"


class ComplianceRegulation(Enum):
    """Compliance regulations - لوائح الامتثال"""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


@dataclass
class Principal:
    """Security principal - المستخدم أو الكيان"""

    id: str
    type: str  # user, service, role, etc.
    roles: set[str] = field(default_factory=set)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """Policy rule definition"""

    effect: Effect
    principals: list[str]  # Can use wildcards like "role:*"
    actions: list[str]
    resources: list[str]
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Policy definition - تعريف السياسة"""

    name: str
    description: str
    rules: list[PolicyRule]
    priority: int = 1
    enabled: bool = True


@dataclass
class ComplianceRule:
    """Compliance rule definition"""

    regulation: ComplianceRegulation
    rule_id: str
    description: str
    validator: Callable[[dict[str, Any]], bool]
    remediation: str


class PolicyEngine:
    """Policy evaluation engine - محرك تقييم السياسات"""

    def __init__(self):
        self.policies: list[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        """Add policy to engine"""
        self.policies.append(policy)
        # Sort by priority (higher priority first)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def evaluate(self, principal: Principal, action: str, resource: str) -> bool:
        """
        Evaluate if principal can perform action on resource

        Returns:
            True if allowed, False if denied
        """
        # Default deny
        result = False

        for policy in self.policies:
            if not policy.enabled:
                continue

            for rule in policy.rules:
                if self._match_rule(rule, principal, action, resource):
                    if rule.effect == Effect.DENY:
                        return False  # DENY always wins
                    elif rule.effect == Effect.ALLOW:
                        result = True

        return result

    def _match_rule(
        self, rule: PolicyRule, principal: Principal, action: str, resource: str
    ) -> bool:
        """Check if rule matches the request"""
        # Check principals
        principal_match = self._match_patterns(
            rule.principals, [f"role:{r}" for r in principal.roles] + [f"{principal.type}:{principal.id}"]
        )

        # Check actions
        action_match = self._match_patterns(rule.actions, [action])

        # Check resources
        resource_match = self._match_patterns(rule.resources, [resource])

        return principal_match and action_match and resource_match

    def _match_patterns(self, patterns: list[str], values: list[str]) -> bool:
        """Match patterns with wildcard support"""
        for pattern in patterns:
            if pattern == "*":
                return True
            for value in values:
                if pattern == value:
                    return True
                # Simple wildcard matching
                if "*" in pattern:
                    pattern_prefix = pattern.split("*")[0]
                    if value.startswith(pattern_prefix):
                        return True
        return False


class SecurityLayer:
    """Security layer for pipeline"""

    def __init__(self, name: str, validator: Callable):
        self.name = name
        self.validator = validator

    async def process(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Process request through security layer"""
        try:
            if await self.validator(request):
                return request
            return None
        except Exception as e:
            logger.error(f"Security layer {self.name} failed: {e}")
            return None


class SecurityPipeline:
    """Multi-layer security pipeline"""

    def __init__(self):
        self.layers: list[SecurityLayer] = []

    def add_layer(self, layer: SecurityLayer) -> None:
        """Add security layer to pipeline"""
        self.layers.append(layer)

    async def process(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Process request through all security layers"""
        current_request = request
        for layer in self.layers:
            result = await layer.process(current_request)
            if result is None:
                logger.warning(f"Request rejected by layer: {layer.name}")
                return None
            current_request = result
        return current_request


class DataGovernance:
    """Data governance and classification"""

    def should_encrypt(self, classification: DataClassification) -> bool:
        """Check if data should be encrypted"""
        return classification in [DataClassification.CONFIDENTIAL, DataClassification.HIGHLY_RESTRICTED]

    def is_location_allowed(self, classification: DataClassification, location: str) -> bool:
        """Check if data can be stored in location"""
        if classification == DataClassification.HIGHLY_RESTRICTED:
            # Highly restricted data cannot be stored in any location
            return False
        return True

    def get_retention_days(self, classification: DataClassification) -> int:
        """Get retention period in days"""
        retention_map = {
            DataClassification.PUBLIC: 365 * 7,  # 7 years
            DataClassification.INTERNAL: 365 * 3,  # 3 years
            DataClassification.CONFIDENTIAL: 365 * 2,  # 2 years
            DataClassification.HIGHLY_RESTRICTED: 365,  # 1 year
        }
        return retention_map.get(classification, 365)


class ComplianceEngine:
    """Compliance validation engine"""

    def __init__(self):
        self.rules: list[ComplianceRule] = []

    def add_rule(self, rule: ComplianceRule) -> None:
        """Add compliance rule"""
        self.rules.append(rule)

    async def validate(self, regulation: ComplianceRegulation, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate data against compliance rules

        Returns:
            (is_compliant, list of violations)
        """
        violations = []
        for rule in self.rules:
            if rule.regulation == regulation:
                try:
                    if not rule.validator(data):
                        violations.append(f"{rule.rule_id}: {rule.description}")
                except Exception as e:
                    logger.error(f"Compliance rule {rule.rule_id} failed: {e}")
                    violations.append(f"{rule.rule_id}: Error - {e!s}")

        return len(violations) == 0, violations


class PolicyBoundary:
    """
    Policy boundary implementation - تطبيق حدود السياسات

    Provides:
    - Policy engine for authorization
    - Security pipeline for multi-layer security
    - Data governance for data classification
    - Compliance engine for regulatory compliance
    """

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.security_pipeline = SecurityPipeline()
        self.data_governance = DataGovernance()
        self.compliance_engine = ComplianceEngine()

    def setup_default_security_layers(self) -> None:
        """Setup default security layers"""

        async def validate_tls(request: dict[str, Any]) -> bool:
            """Validate TLS/HTTPS"""
            return request.get("is_secure", False)

        async def validate_authentication(request: dict[str, Any]) -> bool:
            """Validate authentication token"""
            return "token" in request and request["token"] is not None

        async def validate_authorization(request: dict[str, Any]) -> bool:
            """Validate authorization"""
            principal = request.get("principal")
            action = request.get("action")
            resource = request.get("resource")

            if not all([principal, action, resource]):
                return False

            return self.policy_engine.evaluate(principal, action, resource)

        async def validate_input(request: dict[str, Any]) -> bool:
            """Validate input data"""
            data = request.get("data", {})
            # Basic validation - can be extended
            return isinstance(data, dict)

        self.security_pipeline.add_layer(SecurityLayer("tls", validate_tls))
        self.security_pipeline.add_layer(SecurityLayer("authentication", validate_authentication))
        self.security_pipeline.add_layer(SecurityLayer("authorization", validate_authorization))
        self.security_pipeline.add_layer(SecurityLayer("input_validation", validate_input))


# Singleton instance
_policy_boundary: PolicyBoundary | None = None


def get_policy_boundary() -> PolicyBoundary:
    """
    Get or create policy boundary singleton

    Returns:
        PolicyBoundary instance
    """
    global _policy_boundary
    if _policy_boundary is None:
        _policy_boundary = PolicyBoundary()
    return _policy_boundary
