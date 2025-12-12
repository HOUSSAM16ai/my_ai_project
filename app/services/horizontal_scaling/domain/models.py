"""
Horizontal Scaling Domain Models
================================

Core entities and value objects for the Horizontal Scaling system.
Pure Python, no external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict


class LoadBalancingAlgorithm(Enum):
    """Algorithms for load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LATENCY_BASED = "latency_based"
    CONSISTENT_HASH = "consistent_hash"
    GEOGRAPHIC = "geographic"
    INTELLIGENT_AI = "intelligent_ai"


class ServerState(Enum):
    """Operational state of a server."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"  # No new requests accepted
    OFFLINE = "offline"


class ScalingEvent(Enum):
    """Types of scaling events."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"  # Add servers
    SCALE_IN = "scale_in"  # Remove servers
    NO_ACTION = "no_action"


class RegionZone(Enum):
    """Geographic regions for distribution."""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EUROPE = "europe"
    ASIA = "asia"
    SOUTH_AMERICA = "south-america"
    AFRICA = "africa"
    AUSTRALIA = "australia"


@dataclass
class Server:
    """Represents a server node in the cluster."""
    server_id: str
    name: str
    ip_address: str
    port: int
    region: RegionZone
    state: ServerState
    weight: int = 100
    max_connections: int = 1000
    active_connections: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_health_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Is the server available to accept new requests?"""
        return self.state == ServerState.HEALTHY and self.active_connections < self.max_connections

    @property
    def load_factor(self) -> float:
        """Current load factor (0.0 - 1.0)."""
        if self.max_connections == 0:
            return 0.0
        return self.active_connections / self.max_connections


@dataclass
class ScalingMetrics:
    """Metrics snapshot for scaling decisions."""
    timestamp: datetime
    total_servers: int
    active_servers: int
    total_requests_per_second: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_latency_ms: float
    error_rate: float
    scaling_recommendation: ScalingEvent


@dataclass
class ConsistentHashNode:
    """A node in the consistent hash ring."""
    hash_value: int
    server_id: str
    is_virtual: bool = False
