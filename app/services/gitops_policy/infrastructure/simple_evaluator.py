"""Simple policy evaluator implementation."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from ..domain.models import Policy, PolicyViolation, ResourceType
from ..domain.ports import PolicyEvaluator

logger = logging.getLogger(__name__)


class SimplePolicyEvaluator(PolicyEvaluator):
    """Simple rule-based policy evaluator."""

    def evaluate(
        self, resource: dict[str, Any], policies: list[Policy]
    ) -> list[PolicyViolation]:
        """Evaluate resource against policies."""
        violations = []

        for policy in policies:
            if not policy.enabled:
                continue

            # Check if policy applies to this resource type
            resource_type_str = resource.get("kind", "").lower()
            try:
                resource_type = ResourceType(resource_type_str)
            except ValueError:
                continue

            if policy.resource_types and resource_type not in policy.resource_types:
                continue

            # Evaluate rules
            for rule in policy.rules:
                violation = self._evaluate_rule(resource, rule, policy)
                if violation:
                    violations.append(violation)

        return violations

    def _evaluate_rule(
        self, resource: dict[str, Any], rule: dict[str, Any], policy: Policy
    ) -> PolicyViolation | None:
        """Evaluate a single rule."""
        # Simple rule evaluation logic
        field = rule.get("field")
        operator = rule.get("operator")
        expected = rule.get("value")

        if not field or not operator:
            return None

        actual = self._get_nested_field(resource, field)

        violated = False
        if operator == "equals" and actual != expected:
            violated = True
        elif operator == "not_equals" and actual == expected:
            violated = True
        elif operator == "exists" and actual is None:
            violated = True

        if violated:
            return PolicyViolation(
                violation_id=str(uuid.uuid4()),
                policy_id=policy.policy_id,
                resource_name=resource.get("metadata", {}).get("name", "unknown"),
                resource_type=ResourceType(resource.get("kind", "deployment").lower()),
                message=f"Rule violation: {field} {operator} {expected}",
                severity=rule.get("severity", "medium"),
                timestamp=datetime.now(UTC),
            )

        return None

    def _get_nested_field(self, obj: dict[str, Any], field_path: str) -> Any:
        """Get nested field value using dot notation."""
        parts = field_path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
