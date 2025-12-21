"""
Orchestration Domain Models
============================
Domain entities for Kubernetes orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PodPhase(Enum):
    """Pod lifecycle phases"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    UNKNOWN = 'unknown'


class NodeState(Enum):
    """Node states"""
    READY = 'ready'
    NOT_READY = 'not_ready'
    UNKNOWN = 'unknown'
    CORDONED = 'cordoned'


class ConsensusRole(Enum):
    """Raft consensus roles"""
    LEADER = 'leader'
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'


class ScalingDirection(Enum):
    """Auto-scaling direction"""
    UP = 'up'
    DOWN = 'down'
    NONE = 'none'


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
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_restart: datetime | None = None

    def mark_running(self) ->None:
        """Mark pod as running"""
        self.phase = PodPhase.RUNNING


@dataclass
class Node:
    """Kubernetes Node entity"""
    node_id: str
    name: str
    state: NodeState
    cpu_capacity: float = 16.0
    memory_capacity: float = 32768.0
    cpu_allocated: float = 0.0
    memory_allocated: float = 0.0
    pods: set[str] = field(default_factory=set)
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

    @property
    def cpu_available(self) ->float:
        return self.cpu_capacity - self.cpu_allocated

    @property
    def memory_available(self) ->float:
        return self.memory_capacity - self.memory_allocated

    def can_fit_pod(self, cpu_request: float, memory_request: float) ->bool:
        return (self.state == NodeState.READY and self.cpu_available >=
            cpu_request and self.memory_available >= memory_request)

    def allocate_pod(self, pod: Pod) ->None:
        self.pods.add(pod.pod_id)
        self.cpu_allocated += pod.cpu_request
        self.memory_allocated += pod.memory_request


@dataclass
class RaftState:
    """Raft consensus state"""
    node_id: str
    role: ConsensusRole
    term: int = 0
    voted_for: str | None = None
    log: list[dict[str, Any]] = field(default_factory=list)
    commit_index: int = 0
    last_applied: int = 0
    votes_received: set[str] = field(default_factory=set)
    election_timeout: float = 5.0
    last_heartbeat_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SelfHealingEvent:
    """Self-healing event record"""
    event_id: str
    event_type: str
    resource_id: str
    timestamp: datetime
    details: dict[str, Any]
    success: bool


@dataclass
class AutoScalingConfig:
    """Auto-scaling configuration"""
    deployment_name: str
    min_replicas: int
    max_replicas: int
    target_cpu_percent: float
    target_memory_percent: float
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    cooldown_seconds: int = 300
