"""Facade for GitOps Policy service."""

import logging
from typing import Any

from .application.gitops_controller import GitOpsController
from .application.policy_manager import PolicyManager
from .domain.models import DriftDetectionResult, GitOpsApplication, Policy, PolicyViolation
from .infrastructure.in_memory_repositories import (
    InMemoryApplicationRepository,
    InMemoryPolicyRepository,
)
from .infrastructure.mock_sync_engine import MockGitOpsSync
from .infrastructure.simple_evaluator import SimplePolicyEvaluator

logger = logging.getLogger(__name__)


class GitOpsPolicyServiceFacade:
    """Unified facade for GitOps Policy service."""

    def __init__(self):
        # Infrastructure
        self._policy_repo = InMemoryPolicyRepository()
        self._app_repo = InMemoryApplicationRepository()
        self._evaluator = SimplePolicyEvaluator()
        self._sync_engine = MockGitOpsSync()

        # Application
        self._policy_manager = PolicyManager(self._policy_repo, self._evaluator)
        self._gitops_controller = GitOpsController(self._app_repo, self._sync_engine)

        logger.info("GitOpsPolicyServiceFacade initialized")

    # Policy Management
    def create_policy(self, policy: Policy) -> Policy:
        """Create a new policy."""
        return self._policy_manager.create_policy(policy)

    def validate_resource(
        self, resource: dict[str, Any]
    ) -> tuple[bool, list[PolicyViolation]]:
        """Validate resource against policies."""
        return self._policy_manager.validate_resource(resource)

    def get_enabled_policies(self) -> list[Policy]:
        """Get all enabled policies."""
        return self._policy_manager.get_enabled_policies()

    # GitOps Management
    def register_application(self, app: GitOpsApplication) -> None:
        """Register GitOps application."""
        self._gitops_controller.register_application(app)

    def sync_application(self, app_id: str) -> bool:
        """Sync application from Git."""
        return self._gitops_controller.sync_application(app_id)

    def detect_drift(self, app_id: str) -> DriftDetectionResult:
        """Detect configuration drift."""
        return self._gitops_controller.detect_drift(app_id)

    def get_out_of_sync_apps(self) -> list[GitOpsApplication]:
        """Get out-of-sync applications."""
        return self._gitops_controller.get_out_of_sync_apps()


# Singleton instance
_facade_instance: GitOpsPolicyServiceFacade | None = None


def get_gitops_policy_service() -> GitOpsPolicyServiceFacade:
    """Get or create singleton facade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = GitOpsPolicyServiceFacade()
    return _facade_instance
