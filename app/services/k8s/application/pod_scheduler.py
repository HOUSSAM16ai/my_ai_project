# app/services/k8s/application/pod_scheduler.py
"""Pod scheduling service"""

from __future__ import annotations

from app.services.k8s.domain.models import Node, Pod, PodPhase
from app.services.k8s.domain.ports import NodeRepositoryPort, PodRepositoryPort


class PodScheduler:
    """
    Pod Scheduler - Assigns pods to nodes

    Responsibilities:
    - Find best node for pod based on resources
    - Schedule pod on selected node
    - Update pod and node states
    """

    def __init__(
        self,
        pod_repo: PodRepositoryPort,
        node_repo: NodeRepositoryPort,
    ):
        self._pod_repo = pod_repo
        self._node_repo = node_repo

    def schedule_pod(self, pod: Pod) -> bool:
        """Schedule a pod on the best available node"""
        best_node = self.find_best_node(pod)

        if not best_node:
            return False

        # Assign pod to node
        pod.node_id = best_node.node_id
        pod.phase = PodPhase.RUNNING

        # Update node resources
        best_node.cpu_used += pod.cpu_request
        best_node.memory_used += pod.memory_request
        best_node.pods.append(pod.pod_id)

        # Save changes
        self._pod_repo.save_pod(pod)
        self._node_repo.save_node(best_node)

        return True

    def find_best_node(self, pod: Pod) -> Node | None:
        """
        Find the best node for a pod

        Strategy:
        1. Filter nodes with enough resources
        2. Prefer nodes with lower utilization
        3. Consider node labels and taints
        """
        nodes = self._node_repo.list_nodes()
        suitable_nodes = []

        for node in nodes:
            # Check if node has enough resources
            available_cpu = node.cpu_allocatable - node.cpu_used
            available_memory = node.memory_allocatable - node.memory_used

            if available_cpu >= pod.cpu_request and available_memory >= pod.memory_request:
                # Calculate utilization score (lower is better)
                cpu_util = node.cpu_used / node.cpu_allocatable if node.cpu_allocatable > 0 else 1.0
                mem_util = (
                    node.memory_used / node.memory_allocatable
                    if node.memory_allocatable > 0
                    else 1.0
                )
                score = (cpu_util + mem_util) / 2

                suitable_nodes.append((node, score))

        if not suitable_nodes:
            return None

        # Sort by score (ascending) and return best node
        suitable_nodes.sort(key=lambda x: x[1])
        return suitable_nodes[0][0]
