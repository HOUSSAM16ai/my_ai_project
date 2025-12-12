"""In-memory repositories for GitOps Policy service."""

from ..domain.models import GitOpsApplication, Policy
from ..domain.ports import ApplicationRepository, PolicyRepository


class InMemoryPolicyRepository(PolicyRepository):
    """In-memory policy storage."""

    def __init__(self):
        self._policies: dict[str, Policy] = {}

    def save_policy(self, policy: Policy) -> None:
        """Save a policy."""
        self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Policy | None:
        """Get policy by ID."""
        return self._policies.get(policy_id)

    def list_policies(self) -> list[Policy]:
        """List all policies."""
        return list(self._policies.values())


class InMemoryApplicationRepository(ApplicationRepository):
    """In-memory application storage."""

    def __init__(self):
        self._applications: dict[str, GitOpsApplication] = {}

    def save_application(self, app: GitOpsApplication) -> None:
        """Save application."""
        self._applications[app.app_id] = app

    def get_application(self, app_id: str) -> GitOpsApplication | None:
        """Get application by ID."""
        return self._applications.get(app_id)

    def list_applications(self) -> list[GitOpsApplication]:
        """List all applications."""
        return list(self._applications.values())
