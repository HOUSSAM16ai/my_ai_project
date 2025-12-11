# app/services/k8s/domain/models.py
"""Domain models for Kubernetes Orchestration"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class PodPhase(Enum):
    """Pod lifecycle phases"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class NodeState(Enum):
    """Node states"""

    READY = "ready"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"
    CORDONED = "cordoned"


class ConsensusRole(Enum):
    """Raft consensus roles"""

    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


class ScalingDirection(Enum):
    """Auto-scaling direction"""

    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class Pod:
    """Kubernetes Pod entity"""

    pod_id: str
    name: str
    namespace: str
    node_id: str
    phase: PodPhase
    container_image: str
    replicas: int = 1
    cpu_request: float = 0.5
    memory_request: float = 512
    cpu_limit: float = 1.0
    memory_limit: float = 1024
    restart_count: int = 0
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_restart: datetime | None = None


@dataclass
class Node:
    """Kubernetes Node entity"""

    node_id: str
    name: str
    state: NodeState
    cpu_capacity: float = 16.0
    memory_capacity: float = 64000
    cpu_allocatable: float = 15.0
    memory_allocatable: float = 60000
    cpu_used: float = 0.0
    memory_used: float = 0.0
    pods: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    taints: list[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RaftState:
    """Raft consensus protocol state"""

    node_id: str
    role: ConsensusRole
    term: int = 0
    voted_for: str | None = None
    commit_index: int = 0
    last_applied: int = 0
    log: list[dict[str, Any]] = field(default_factory=list)
    votes_received: set[str] = field(default_factory=set)
    election_timeout: float = 5.0
    last_heartbeat_time: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AutoScalingConfig:
    """Auto-scaling configuration"""

    config_id: str
    deployment_name: str
    namespace: str
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization: float = 70.0
    target_memory_utilization: float = 80.0
    scale_up_cooldown: int = 60
    scale_down_cooldown: int = 300
    last_scale_time: datetime | None = None


@dataclass
class SelfHealingEvent:
    """Self-healing event record"""

    event_id: str
    timestamp: datetime
    event_type: str
    pod_id: str
    node_id: str
    description: str
    action_taken: str
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
