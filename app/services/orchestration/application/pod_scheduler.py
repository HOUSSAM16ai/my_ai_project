# app/services/orchestration/application/pod_scheduler.py
"""
Pod Scheduler Service
=====================
Single Responsibility: Schedule pods to nodes.
"""

from __future__ import annotations

import hashlib
import time
from typing import Protocol

from app.services.orchestration.domain.models import Node, Pod, PodPhase


class PodRepository(Protocol):
    def save(self, pod: Pod) -> None: ...
    def get(self, pod_id: str) -> Pod | None: ...


class NodeRepository(Protocol):
    def get_all(self) -> list[Node]: ...
    def update(self, node: Node) -> None: ...


class PodScheduler:
    """
    Kubernetes pod scheduler.

    Responsibilities:
    - Find best node for pod
    - Allocate pod to node
    - Load balancing
    """

    def __init__(
        self,
        pod_repository: PodRepository,
        node_repository: NodeRepository,
    ):
        self._pod_repo = pod_repository
        self._node_repo = node_repository

    def schedule_pod(
        self,
        name: str,
        namespace: str,
        container_image: str,
        cpu_request: float = 0.5,
        memory_request: float = 512,
        cpu_limit: float = 1.0,
        memory_limit: float = 1024,
        labels: dict[str, str] | None = None,
    ) -> str:
        """Schedule new pod"""
        # Find best node
        best_node = self._find_best_node(cpu_request, memory_request)

        if not best_node:
            raise RuntimeError("No available nodes for pod")

        # Create pod
        pod_id = self._generate_pod_id(name)
        pod = Pod(
            pod_id=pod_id,
            name=name,
            namespace=namespace,
            node_id=best_node.node_id,
            phase=PodPhase.PENDING,
            container_image=container_image,
            cpu_request=cpu_request,
            memory_request=memory_request,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            labels=labels or {},
        )

        # Allocate to node
        best_node.allocate_pod(pod)
        self._node_repo.update(best_node)

        # Mark as running
        pod.mark_running()
        self._pod_repo.save(pod)

        return pod_id

    def _find_best_node(
        self,
        cpu_request: float,
        memory_request: float,
    ) -> Node | None:
        """Find best node for pod using bin-packing strategy"""
        nodes = self._node_repo.get_all()

        # Filter nodes that can fit the pod
        eligible = [
            n for n in nodes
            if n.can_fit_pod(cpu_request, memory_request)
        ]

        if not eligible:
            return None

        # Best fit: node with least remaining resources (bin-packing)
        return min(
            eligible,
            key=lambda n: n.cpu_available + n.memory_available,
        )

    def _generate_pod_id(self, name: str) -> str:
        """Generate unique pod ID"""
        return hashlib.sha256(
            f"{name}{time.time_ns()}".encode()
        ).hexdigest()[:16]
