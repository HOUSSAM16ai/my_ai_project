# app/services/k8s/infrastructure/in_memory_node_repository.py
"""In-memory Node repository implementation"""

from __future__ import annotations

import threading

from app.services.k8s.domain.models import Node


class InMemoryNodeRepository:
    """In-memory storage for Nodes"""

    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._lock = threading.RLock()

    def save_node(self, node: Node) -> None:
        """Save a node"""
        with self._lock:
            self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Node | None:
        """Get node by ID"""
        with self._lock:
            return self._nodes.get(node_id)

    def list_nodes(self) -> list[Node]:
        """List all nodes"""
        with self._lock:
            return list(self._nodes.values())

    def update_node_resources(self, node_id: str, cpu_used: float, memory_used: float) -> None:
        """Update node resource usage"""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].cpu_used = cpu_used
                self._nodes[node_id].memory_used = memory_used
