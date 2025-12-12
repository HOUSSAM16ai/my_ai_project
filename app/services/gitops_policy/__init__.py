"""GitOps Policy Service - Hexagonal Architecture.

Provides GitOps and Policy-as-Code with:
- Policy enforcement and validation
- GitOps synchronization
- Drift detection
- Multi-environment management
"""

from .facade import GitOpsPolicyServiceFacade, get_gitops_policy_service

__all__ = ["GitOpsPolicyServiceFacade", "get_gitops_policy_service"]
