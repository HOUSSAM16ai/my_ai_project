# app/services/k8s/facade.py
"""
Backward compatible facade for kubernetes_orchestration_service.py

Provides the same API as the original monolithic service
"""

from __future__ import annotations

import threading
from typing import Any

from app.services.k8s.application import (
    AutoScaler,
    ConsensusManager,
    HealthMonitor,
    PodScheduler,
    SelfHealer,
)
from app.services.k8s.domain.models import (
    AutoScalingConfig,
    ConsensusRole,
    Node,
    NodeState,
    Pod,
    PodPhase,
    RaftState,
    ScalingDirection,
    SelfHealingEvent,
)
from app.services.k8s.infrastructure import InMemoryNodeRepository, InMemoryPodRepository

# Re-export models for backward compatibility
__all__ = [
    "KubernetesOrchestrator",
    "get_kubernetes_orchestrator",
    "Pod",
    "Node",
    "PodPhase",
    "NodeState",
    "ConsensusRole",
    "ScalingDirection",
    "RaftState",
    "AutoScalingConfig",
    "SelfHealingEvent",
]


class KubernetesOrchestrator:
    """
    Kubernetes Orchestrator - Backward compatible facade

    Maintains the same API as the original monolithic service
    but delegates to specialized components
    """

    def __init__(self, node_id: str = "node-1"):
        self.node_id = node_id

        # Infrastructure layer
        self._pod_repo = InMemoryPodRepository()
        self._node_repo = InMemoryNodeRepository()

        # Application layer
        self._scheduler = PodScheduler(self._pod_repo, self._node_repo)
        self._auto_scaler = AutoScaler(self._pod_repo, self._node_repo)
        self._self_healer = SelfHealer(self._pod_repo, self._node_repo)
        self._consensus = ConsensusManager(node_id)

        # Health monitor with callbacks
        self._health_monitor = HealthMonitor(
            self._pod_repo,
            self._node_repo,
            on_pod_failure=self._self_healer.heal_failed_pod,
            on_node_failure=self._self_healer.evacuate_node,
        )

        # Initialize cluster
        self._initialize_cluster()

        # Start services
        self._health_monitor.start_monitoring()
        self._consensus.start_consensus_protocol()

    def _initialize_cluster(self):
        """Initialize cluster with default nodes"""
        for i in range(1, 4):
            node = Node(
                node_id=f"node-{i}",
                name=f"k8s-node-{i}",
                state=NodeState.READY,
                labels={
                    "zone": f"zone-{(i % 3) + 1}",
                    "node-type": "worker",
                },
            )
            self._node_repo.save_node(node)

    # ======================================================================================
    # POD OPERATIONS
    # ======================================================================================

    def schedule_pod(self, pod: Pod) -> bool:
        """Schedule a pod on a suitable node"""
        return self._scheduler.schedule_pod(pod)

    def get_pod_status(self, pod_id: str) -> Pod | None:
        """Get pod status"""
        return self._pod_repo.get_pod(pod_id)

    # ======================================================================================
    # NODE OPERATIONS
    # ======================================================================================

    def get_node_status(self, node_id: str) -> Node | None:
        """Get node status"""
        return self._node_repo.get_node(node_id)

    # ======================================================================================
    # AUTO-SCALING
    # ======================================================================================

    def configure_autoscaling(self, config: AutoScalingConfig):
        """Configure auto-scaling for a deployment"""
        self._auto_scaler.configure_autoscaling(config)

    def check_autoscaling(self):
        """Check and apply auto-scaling rules"""
        self._auto_scaler.check_autoscaling()

    # ======================================================================================
    # CONSENSUS (RAFT)
    # ======================================================================================

    def get_raft_state(self) -> RaftState:
        """Get current Raft state"""
        return self._consensus.get_raft_state()

    def append_log_entry(self, entry: dict[str, Any]) -> bool:
        """Append entry to Raft log"""
        return self._consensus.append_log_entry(entry)

    # ======================================================================================
    # SELF-HEALING
    # ======================================================================================

    def get_healing_events(self, limit: int = 100) -> list[SelfHealingEvent]:
        """Get recent healing events"""
        return self._self_healer.get_healing_events(limit)

    # ======================================================================================
    # CLUSTER STATS
    # ======================================================================================

    def get_cluster_stats(self) -> dict[str, Any]:
        """Get cluster statistics"""
        pods = self._pod_repo.list_pods()
        nodes = self._node_repo.list_nodes()

        total_pods = len(pods)
        running_pods = sum(1 for p in pods if p.phase == PodPhase.RUNNING)
        failed_pods = sum(1 for p in pods if p.phase == PodPhase.FAILED)

        total_cpu = sum(n.cpu_capacity for n in nodes)
        total_memory = sum(n.memory_capacity for n in nodes)
        used_cpu = sum(n.cpu_used for n in nodes)
        used_memory = sum(n.memory_used for n in nodes)

        raft_state = self._consensus.get_raft_state()

        return {
            "total_nodes": len(nodes),
            "ready_nodes": sum(1 for n in nodes if n.state == NodeState.READY),
            "total_pods": total_pods,
            "running_pods": running_pods,
            "failed_pods": failed_pods,
            "cpu_utilization": (used_cpu / total_cpu * 100) if total_cpu > 0 else 0,
            "memory_utilization": (used_memory / total_memory * 100) if total_memory > 0 else 0,
            "raft_role": raft_state.role.value,
            "raft_term": raft_state.term,
            "healing_events": len(self._self_healer.get_healing_events()),
        }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_k8s_orchestrator_instance: KubernetesOrchestrator | None = None
_k8s_lock = threading.Lock()


def get_kubernetes_orchestrator() -> KubernetesOrchestrator:
    """Get singleton instance of Kubernetes Orchestrator"""
    global _k8s_orchestrator_instance

    if _k8s_orchestrator_instance is None:
        with _k8s_lock:
            if _k8s_orchestrator_instance is None:
                _k8s_orchestrator_instance = KubernetesOrchestrator()

    return _k8s_orchestrator_instance
