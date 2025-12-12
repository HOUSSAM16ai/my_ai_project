"""Domain models for GitOps Policy service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PolicyEnforcementMode(Enum):
    """Policy enforcement modes."""

    ENFORCE = "enforce"
    AUDIT = "audit"
    WARN = "warn"


class ResourceType(Enum):
    """Resource types."""

    DEPLOYMENT = "deployment"
    SERVICE = "service"
    CONFIG_MAP = "configmap"
    SECRET = "secret"
    INGRESS = "ingress"
    NAMESPACE = "namespace"


class SyncStatus(Enum):
    """GitOps sync status."""

    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    SYNCING = "syncing"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Policy:
    """Policy definition."""

    policy_id: str
    name: str
    description: str
    enforcement_mode: PolicyEnforcementMode
    rules: list[dict[str, Any]] = field(default_factory=list)
    resource_types: list[ResourceType] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime | None = None


@dataclass
class PolicyViolation:
    """Policy violation record."""

    violation_id: str
    policy_id: str
    resource_name: str
    resource_type: ResourceType
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    timestamp: datetime


@dataclass
class GitOpsApplication:
    """GitOps application definition."""

    app_id: str
    name: str
    git_repo: str
    git_branch: str
    target_namespace: str
    sync_status: SyncStatus
    last_sync: datetime | None = None
    auto_sync: bool = True


@dataclass
class DriftDetectionResult:
    """Drift detection result."""

    has_drift: bool
    drifted_resources: list[str] = field(default_factory=list)
    detected_at: datetime | None = None
