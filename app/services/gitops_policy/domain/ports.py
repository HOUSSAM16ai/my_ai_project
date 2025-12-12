"""Domain ports for GitOps Policy service."""

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    DriftDetectionResult,
    GitOpsApplication,
    Policy,
    PolicyViolation,
)


class PolicyRepository(ABC):
    """Repository for policy management."""

    @abstractmethod
    def save_policy(self, policy: Policy) -> None:
        """Save a policy."""
        pass

    @abstractmethod
    def get_policy(self, policy_id: str) -> Policy | None:
        """Get policy by ID."""
        pass

    @abstractmethod
    def list_policies(self) -> list[Policy]:
        """List all policies."""
        pass


class PolicyEvaluator(ABC):
    """Policy evaluation interface."""

    @abstractmethod
    def evaluate(
        self, resource: dict[str, Any], policies: list[Policy]
    ) -> list[PolicyViolation]:
        """Evaluate resource against policies."""
        pass


class GitOpsSync(ABC):
    """GitOps synchronization interface."""

    @abstractmethod
    def sync_application(self, app: GitOpsApplication) -> bool:
        """Sync application from Git."""
        pass

    @abstractmethod
    def detect_drift(self, app: GitOpsApplication) -> DriftDetectionResult:
        """Detect configuration drift."""
        pass


class ApplicationRepository(ABC):
    """Repository for GitOps applications."""

    @abstractmethod
    def save_application(self, app: GitOpsApplication) -> None:
        """Save application."""
        pass

    @abstractmethod
    def get_application(self, app_id: str) -> GitOpsApplication | None:
        """Get application by ID."""
        pass

    @abstractmethod
    def list_applications(self) -> list[GitOpsApplication]:
        """List all applications."""
        pass
