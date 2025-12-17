"""
Node Manager Service
====================
Single Responsibility: Manage cluster nodes.
"""
from __future__ import annotations
import hashlib
from datetime import datetime
from typing import Protocol
from app.services.orchestration.domain.models import Node, NodeState


class NodeRepository(Protocol):

    def save(self, node: Node) ->None:
        ...

    def get(self, node_id: str) ->(Node | None):
        ...

    def get_all(self) ->list[Node]:
        ...

    def update(self, node: Node) ->None:
        ...


class NodeManager:
    """
    Cluster node manager.

    Responsibilities:
    - Add/remove nodes
    - Monitor node health
    - Update node state
    """

    def __init__(self, node_repository: NodeRepository):
        self._node_repo = node_repository

    def add_node(self, name: str, cpu_capacity: float=16.0, memory_capacity:
        float=32768.0, labels: (dict[str, str] | None)=None) ->str:
        """Add new node to cluster"""
        node_id = hashlib.sha256(name.encode()).hexdigest()[:16]
        node = Node(node_id=node_id, name=name, state=NodeState.READY,
            cpu_capacity=cpu_capacity, memory_capacity=memory_capacity,
            labels=labels or {})
        self._node_repo.save(node)
        return node_id

    def get_node(self, node_id: str) ->(Node | None):
        """Get node by ID"""
        return self._node_repo.get(node_id)

    def get_all_nodes(self) ->list[Node]:
        """Get all nodes"""
        return self._node_repo.get_all()

    def update_node_heartbeat(self, node_id: str) ->None:
        """Update node heartbeat"""
        node = self._node_repo.get(node_id)
        if node:
            node.last_heartbeat = datetime.utcnow()
            self._node_repo.update(node)
