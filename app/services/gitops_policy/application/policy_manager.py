"""Policy management application service."""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any
from ..domain.models import Policy, PolicyViolation
from ..domain.ports import PolicyEvaluator, PolicyRepository
logger = logging.getLogger(__name__)


class PolicyManager:
    """Manages policies and enforcement."""

    def __init__(self, repository: PolicyRepository, evaluator: PolicyEvaluator
        ):
        self.repository = repository
        self.evaluator = evaluator

    def create_policy(self, policy: Policy) ->Policy:
        """Create a new policy."""
        policy.created_at = datetime.now(UTC)
        self.repository.save_policy(policy)
        logger.info(f'Created policy: {policy.name}')
        return policy

    def get_enabled_policies(self) ->list[Policy]:
        """Get all enabled policies."""
        all_policies = self.repository.list_policies()
        return [p for p in all_policies if p.enabled]

    def validate_resource(self, resource: dict[str, Any]) ->tuple[bool,
        list[PolicyViolation]]:
        """Validate resource against all enabled policies."""
        policies = self.get_enabled_policies()
        violations = self.evaluator.evaluate(resource, policies)
        is_valid = not any(v.severity in ['critical', 'high'] for v in
            violations)
        if violations:
            logger.warning(
                f'Resource validation found {len(violations)} violations')
        return is_valid, violations
