from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProtocolType(Enum):
    """Supported protocol types"""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class RoutingStrategy(Enum):
    """Routing strategies for requests"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    LATENCY_BASED = "latency_based"
    COST_OPTIMIZED = "cost_optimized"
    INTELLIGENT = "intelligent"  # ML-based routing


class ModelProvider(Enum):
    """AI Model providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"


class CacheStrategy(Enum):
    """Caching strategies"""

    NO_CACHE = "no_cache"
    REDIS = "redis"
    MEMORY = "memory"
    DISTRIBUTED = "distributed"
    INTELLIGENT = "intelligent"  # ML-based caching


@dataclass
class GatewayRoute:
    """Gateway route configuration"""

    route_id: str
    path_pattern: str
    methods: list[str]
    upstream_service: str
    protocol: ProtocolType
    auth_required: bool = True
    rate_limit: int | None = None
    cache_ttl: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UpstreamService:
    """Upstream service configuration"""

    service_id: str
    name: str
    base_url: str
    health_check_url: str
    protocol: ProtocolType
    weight: int = 100
    max_connections: int = 1000
    timeout_ms: int = 30000
    circuit_breaker_threshold: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Routing decision result"""

    service_id: str
    base_url: str
    protocol: ProtocolType
    estimated_latency_ms: float
    estimated_cost: float
    confidence_score: float
    reasoning: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalancerState:
    """Load balancer state tracking"""

    service_id: str
    active_connections: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    last_health_check: datetime | None = None
    is_healthy: bool = True


@dataclass
class PolicyRule:
    """Policy enforcement rule"""

    rule_id: str
    name: str
    condition: str  # Expression to evaluate
    action: str  # allow, deny, rate_limit, transform
    priority: int = 100
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
