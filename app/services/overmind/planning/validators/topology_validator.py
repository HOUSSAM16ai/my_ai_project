# app/overmind/planning/validators/topology_validator.py
"""
Topology validator using topological sort.

Validates graph topology, detects cycles, and computes depth map.
Complexity: CC ≤ 5 per method
"""

from collections import deque
from typing import Any

from .graph_builder import GraphData


class TopologyValidator:
    """Validates graph topology and detects cycles."""

    def validate(self, graph_data: GraphData) -> tuple[list[Any], dict[str, Any]]:
        """
        Validate graph topology.

        Complexity: CC=5
        Returns: (issues, metadata)
        """
        from ..schemas import PlanValidationIssue

        issues = []

        roots = self._find_roots(graph_data)
        if not roots:
            issues.append(
                PlanValidationIssue(code="NO_ROOTS", message="No root tasks (possible cycle)")
            )
            return issues, {}

        topo_order, depth_map = self._topological_sort(graph_data, roots)

        if len(topo_order) != graph_data.task_count:
            cyclic_nodes = self._find_cyclic_nodes(graph_data, topo_order)
            issues.append(
                PlanValidationIssue(
                    code="CYCLE_DETECTED",
                    message="Dependency cycle detected",
                    detail={"nodes": cyclic_nodes},
                )
            )

        metadata = {
            "topo_order": topo_order,
            "depth_map": depth_map,
            "roots": roots,
        }

        return issues, metadata

    def _find_roots(self, graph_data: GraphData) -> list[str]:
        """
        Find root tasks (tasks with no dependencies).

        Complexity: CC=2
        """
        return [tid for tid, deg in graph_data.indegree.items() if deg == 0]

    def _topological_sort(
        self, graph_data: GraphData, roots: list[str]
    ) -> tuple[list[str], dict[str, int]]:
        """
        Perform topological sort and compute depth map.

        Complexity: CC=4
        """
        queue = deque(roots)
        topo_order = []
        depth_map = dict.fromkeys(graph_data.id_map, 0)
        remaining = graph_data.indegree.copy()

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            for child in graph_data.adjacency[node]:
                remaining[child] -= 1
                depth_map[child] = max(depth_map[child], depth_map[node] + 1)

                if remaining[child] == 0:
                    queue.append(child)

        return topo_order, depth_map

    def _find_cyclic_nodes(self, graph_data: GraphData, topo_order: list[str]) -> list[str]:
        """
        Find nodes involved in cycles.

        Complexity: CC=2
        """
        processed = set(topo_order)
        return [tid for tid in graph_data.id_map if tid not in processed]
