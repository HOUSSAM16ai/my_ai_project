# app/services/gitops_policy_service.py
# ======================================================================================
# LEGACY SHIM - Redirects to Hexagonal Architecture
# ======================================================================================
# ✅ REFACTORED: 520 lines → 50 lines (90% reduction)
#
# New code should use:
#   from app.services.gitops_policy import get_gitops_policy_service

import logging
from typing import Any

from .gitops_policy import get_gitops_policy_service
from .gitops_policy.domain import (
    GitOpsApplication,
    Policy,
    PolicyEnforcementMode,
    ResourceType,
    SyncStatus,
)

logger = logging.getLogger(__name__)

# Singleton facade
_service = get_gitops_policy_service()


class GitOpsPolicyService:
    """Legacy wrapper for backward compatibility."""

    @staticmethod
    def create_policy(policy: Policy) -> Policy:
        """Create a new policy."""
        return _service.create_policy(policy)

    @staticmethod
    def validate_resource(resource: dict[str, Any]):
        """Validate resource against policies."""
        return _service.validate_resource(resource)

    @staticmethod
    def register_application(app: GitOpsApplication) -> None:
        """Register GitOps application."""
        _service.register_application(app)

    @staticmethod
    def sync_application(app_id: str) -> bool:
        """Sync application from Git."""
        return _service.sync_application(app_id)


# Module-level functions
def create_policy(policy: Policy) -> Policy:
    """Create a new policy."""
    return _service.create_policy(policy)


def validate_resource(resource: dict[str, Any]):
    """Validate resource against policies."""
    return _service.validate_resource(resource)
