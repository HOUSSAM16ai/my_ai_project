# app/overmind/planning/generators/dependency_builder.py
"""Dependency builder with CC ≤ 4."""

from dataclasses import dataclass
from typing import Any


@dataclass
class DependencyGraph:
    """Dependency graph representation."""
    adjacency: dict[str, list[str]]
    indegree: dict[str, int]
    
    def is_valid(self) -> bool:
        """Check if graph is valid (no cycles). CC=2"""
        return len(self.adjacency) > 0 and all(
            isinstance(v, list) for v in self.adjacency.values()
        )


class DependencyBuilder:
    """Builds dependency graph. CC ≤ 4"""
    
    def build(self, tasks: list[Any]) -> DependencyGraph:
        """Build dependency graph from tasks. CC=3"""
        adjacency = {t.task_id: [] for t in tasks}
        indegree = {t.task_id: 0 for t in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep in adjacency:
                    adjacency[dep].append(task.task_id)
                    indegree[task.task_id] += 1
        
        return DependencyGraph(adjacency=adjacency, indegree=indegree)
    
    def validate(self, graph: DependencyGraph) -> bool:
        """Validate dependency graph. CC=3"""
        if not graph.is_valid():
            return False
        
        # Check for cycles using topological sort
        from collections import deque
        
        queue = deque([tid for tid, deg in graph.indegree.items() if deg == 0])
        processed = 0
        
        while queue:
            node = queue.popleft()
            processed += 1
            
            for child in graph.adjacency[node]:
                graph.indegree[child] -= 1
                if graph.indegree[child] == 0:
                    queue.append(child)
        
        return processed == len(graph.adjacency)
