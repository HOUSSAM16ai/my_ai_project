from enum import Enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class DataDomainType(Enum):
    """Data domain types"""

    USER_MANAGEMENT = "user_management"
    MISSION_ORCHESTRATION = "mission_orchestration"
    TASK_EXECUTION = "task_execution"
    ANALYTICS = "analytics"
    SECURITY = "security"
    NOTIFICATION = "notification"
    CONTENT_MANAGEMENT = "content_management"
    BILLING = "billing"


class DataProductStatus(Enum):
    """Data product lifecycle status"""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class SchemaCompatibility(Enum):
    """Schema evolution compatibility"""

    BACKWARD = "backward"  # New schema can read old data
    FORWARD = "forward"  # Old schema can read new data
    FULL = "full"  # Both backward and forward compatible
    BREAKING = "breaking"  # Incompatible changes


class GovernanceLevel(Enum):
    """Governance enforcement level"""

    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class DataContract:
    """Data contract definition"""

    contract_id: str
    domain: DataDomainType
    name: str
    description: str
    schema_version: str
    schema_definition: dict[str, Any]
    compatibility_mode: SchemaCompatibility
    owners: list[str]
    consumers: list[str]
    sla_guarantees: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: DataProductStatus = DataProductStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProduct:
    """Data product - business-oriented data asset"""

    product_id: str
    name: str
    domain: DataDomainType
    description: str
    owner_team: str
    contracts: list[str]  # Contract IDs
    quality_metrics: dict[str, float]
    access_patterns: list[str]
    lineage: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: DataProductStatus = DataProductStatus.ACTIVE


@dataclass
class BoundedContext:
    """Bounded context for domain isolation"""

    context_id: str
    domain: DataDomainType
    name: str
    description: str
    data_products: list[str]
    upstream_contexts: list[str]
    downstream_contexts: list[str]
    governance_policies: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GovernancePolicy:
    """Governance policy definition"""

    policy_id: str
    name: str
    description: str
    level: GovernanceLevel
    rules: list[dict[str, Any]]
    applicable_domains: list[DataDomainType]
    enforcement_actions: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    enabled: bool = True


@dataclass
class DataQualityMetrics:
    """Data quality metrics"""

    product_id: str
    timestamp: datetime
    completeness: float  # 0-1
    accuracy: float  # 0-1
    consistency: float  # 0-1
    timeliness: float  # 0-1
    freshness_seconds: float
    volume: int
    error_rate: float


@dataclass
class SchemaEvolution:
    """Schema evolution tracking"""

    evolution_id: str
    contract_id: str
    from_version: str
    to_version: str
    changes: list[dict[str, Any]]
    compatibility: SchemaCompatibility
    migration_scripts: list[str]
    validated_at: datetime
    deployed_at: datetime | None = None
