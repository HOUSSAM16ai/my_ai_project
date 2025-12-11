# app/services/k8s/domain/ports.py
"""Domain ports (interfaces) for Kubernetes Orchestration"""

from __future__ import annotations

from typing import Any, Protocol

from app.services.k8s.domain.models import (
    AutoScalingConfig,
    Node,
    Pod,
    RaftState,
    ScalingDirection,
    SelfHealingEvent,
)


class PodRepositoryPort(Protocol):
    """Port for Pod storage operations"""

    def save_pod(self, pod: Pod) -> None:
        """Save a pod"""
        ...

    def get_pod(self, pod_id: str) -> Pod | None:
        """Get pod by ID"""
        ...

    def list_pods(self, namespace: str | None = None) -> list[Pod]:
        """List all pods, optionally filtered by namespace"""
        ...

    def delete_pod(self, pod_id: str) -> bool:
        """Delete a pod"""
        ...

    def update_pod_phase(self, pod_id: str, phase: Any) -> None:
        """Update pod phase"""
        ...


class NodeRepositoryPort(Protocol):
    """Port for Node storage operations"""

    def save_node(self, node: Node) -> None:
        """Save a node"""
        ...

    def get_node(self, node_id: str) -> Node | None:
        """Get node by ID"""
        ...

    def list_nodes(self) -> list[Node]:
        """List all nodes"""
        ...

    def update_node_resources(self, node_id: str, cpu_used: float, memory_used: float) -> None:
        """Update node resource usage"""
        ...


class SchedulerPort(Protocol):
    """Port for Pod scheduling"""

    def schedule_pod(self, pod: Pod) -> bool:
        """Schedule a pod on a suitable node"""
        ...

    def find_best_node(self, pod: Pod) -> Node | None:
        """Find the best node for a pod"""
        ...


class AutoScalerPort(Protocol):
    """Port for auto-scaling operations"""

    def configure_autoscaling(self, config: AutoScalingConfig) -> None:
        """Configure auto-scaling for a deployment"""
        ...

    def check_autoscaling(self) -> None:
        """Check and apply auto-scaling rules"""
        ...

    def scale_deployment(self, config: AutoScalingConfig, direction: ScalingDirection) -> None:
        """Scale a deployment up or down"""
        ...


class SelfHealingPort(Protocol):
    """Port for self-healing operations"""

    def heal_failed_pod(self, pod: Pod) -> None:
        """Heal a failed pod"""
        ...

    def evacuate_node(self, node: Node) -> None:
        """Evacuate pods from a node"""
        ...

    def record_healing_event(self, event: SelfHealingEvent) -> None:
        """Record a healing event"""
        ...

    def get_healing_events(self, limit: int = 100) -> list[SelfHealingEvent]:
        """Get recent healing events"""
        ...


class HealthMonitorPort(Protocol):
    """Port for health monitoring"""

    def check_pod_health(self) -> None:
        """Check health of all pods"""
        ...

    def check_node_health(self) -> None:
        """Check health of all nodes"""
        ...

    def start_monitoring(self) -> None:
        """Start continuous health monitoring"""
        ...


class ConsensusPort(Protocol):
    """Port for distributed consensus (Raft)"""

    def get_raft_state(self) -> RaftState:
        """Get current Raft state"""
        ...

    def append_log_entry(self, entry: dict[str, Any]) -> bool:
        """Append entry to Raft log"""
        ...

    def send_heartbeats(self) -> None:
        """Send heartbeats to followers"""
        ...

    def conduct_election(self) -> None:
        """Conduct leader election"""
        ...

    def start_consensus_protocol(self) -> None:
        """Start consensus protocol"""
        ...
