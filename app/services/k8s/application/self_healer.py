# app/services/k8s/application/self_healer.py
"""Self-healing service"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime

from app.services.k8s.domain.models import Node, NodeState, Pod, PodPhase, SelfHealingEvent
from app.services.k8s.domain.ports import NodeRepositoryPort, PodRepositoryPort


class SelfHealer:
    """
    Self-Healer - Automatic recovery from failures

    Responsibilities:
    - Detect failed pods and restart them
    - Evacuate pods from unhealthy nodes
    - Record healing events
    """

    def __init__(
        self,
        pod_repo: PodRepositoryPort,
        node_repo: NodeRepositoryPort,
    ):
        self._pod_repo = pod_repo
        self._node_repo = node_repo
        self._healing_events: deque[SelfHealingEvent] = deque(maxlen=1000)

    def heal_failed_pod(self, pod: Pod) -> None:
        """
        Heal a failed pod

        Strategy:
        1. Try to restart on same node (up to 3 times)
        2. If restart fails, reschedule on different node
        """
        pod.restart_count += 1
        pod.last_restart = datetime.now(UTC)

        if pod.restart_count <= 3:
            # Try restart on same node
            pod.phase = PodPhase.RUNNING
            action = f"Restarted pod on same node (attempt {pod.restart_count})"
            success = True
        else:
            # Reschedule on different node
            old_node_id = pod.node_id
            pod.node_id = ""  # Will be reassigned by scheduler
            pod.phase = PodPhase.PENDING
            action = f"Rescheduled pod from node {old_node_id} after {pod.restart_count} failures"
            success = True

        # Save pod
        self._pod_repo.save_pod(pod)

        # Record healing event
        event = SelfHealingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            event_type="pod_failure",
            pod_id=pod.pod_id,
            node_id=pod.node_id,
            description=f"Pod {pod.name} failed and was healed",
            action_taken=action,
            success=success,
            metadata={"restart_count": pod.restart_count},
        )
        self._healing_events.append(event)

    def evacuate_node(self, node: Node) -> None:
        """
        Evacuate all pods from a node

        Used when node becomes unhealthy
        """
        # Mark node as cordoned
        node.state = NodeState.CORDONED
        self._node_repo.save_node(node)

        # Get all pods on this node
        pods = [p for p in self._pod_repo.list_pods() if p.node_id == node.node_id]

        for pod in pods:
            # Reschedule pod
            pod.node_id = ""
            pod.phase = PodPhase.PENDING
            self._pod_repo.save_pod(pod)

            # Record event
            event = SelfHealingEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                event_type="node_evacuation",
                pod_id=pod.pod_id,
                node_id=node.node_id,
                description=f"Evacuated pod {pod.name} from unhealthy node {node.name}",
                action_taken="Rescheduled pod to different node",
                success=True,
                metadata={"reason": "node_unhealthy"},
            )
            self._healing_events.append(event)

        # Clear node's pod list
        node.pods.clear()
        node.cpu_used = 0.0
        node.memory_used = 0.0
        self._node_repo.save_node(node)

    def get_healing_events(self, limit: int = 100) -> list[SelfHealingEvent]:
        """Get recent healing events"""
        return list(self._healing_events)[-limit:]
