# app/services/orchestration/infrastructure/in_memory_repository.py
"""
In-Memory Repository Implementations
=====================================
Concrete implementations of orchestration repository ports.
"""

from __future__ import annotations

import threading

from app.services.orchestration.domain.models import Node, Pod, SelfHealingEvent


class InMemoryPodRepository:
    """In-memory pod repository"""

    def __init__(self):
        self._pods: dict[str, Pod] = {}
        self._pods_by_node: dict[str, list[Pod]] = {}
        self._lock = threading.RLock()

    def save(self, pod: Pod) -> None:
        """Save pod"""
        with self._lock:
            self._pods[pod.pod_id] = pod
            if pod.node_id not in self._pods_by_node:
                self._pods_by_node[pod.node_id] = []
            if pod not in self._pods_by_node[pod.node_id]:
                self._pods_by_node[pod.node_id].append(pod)

    def get(self, pod_id: str) -> Pod | None:
        """Get pod by ID"""
        with self._lock:
            return self._pods.get(pod_id)

    def get_all(self) -> list[Pod]:
        """Get all pods"""
        with self._lock:
            return list(self._pods.values())

    def get_by_node(self, node_id: str) -> list[Pod]:
        """Get pods by node"""
        with self._lock:
            return self._pods_by_node.get(node_id, []).copy()

    def delete(self, pod_id: str) -> None:
        """Delete pod"""
        with self._lock:
            pod = self._pods.pop(pod_id, None)
            if pod:
                node_pods = self._pods_by_node.get(pod.node_id, [])
                if pod in node_pods:
                    node_pods.remove(pod)


class InMemoryNodeRepository:
    """In-memory node repository"""

    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._lock = threading.RLock()

    def save(self, node: Node) -> None:
        """Save node"""
        with self._lock:
            self._nodes[node.node_id] = node

    def get(self, node_id: str) -> Node | None:
        """Get node by ID"""
        with self._lock:
            return self._nodes.get(node_id)

    def get_all(self) -> list[Node]:
        """Get all nodes"""
        with self._lock:
            return list(self._nodes.values())

    def update(self, node: Node) -> None:
        """Update node"""
        with self._lock:
            self._nodes[node.node_id] = node


class InMemoryHealingEventRepository:
    """In-memory healing event repository"""

    def __init__(self):
        self._events: list[SelfHealingEvent] = []
        self._lock = threading.RLock()

    def save(self, event: SelfHealingEvent) -> None:
        """Save healing event"""
        with self._lock:
            self._events.append(event)

    def get_recent(self, limit: int = 100) -> list[SelfHealingEvent]:
        """Get recent events"""
        with self._lock:
            return sorted(
                self._events,
                key=lambda e: e.timestamp,
                reverse=True,
            )[:limit]


__all__ = [
    "InMemoryHealingEventRepository",
    "InMemoryNodeRepository",
    "InMemoryPodRepository",
]
