# app/overmind/planning/validators/graph_builder.py
"""
Graph data structure builder using Builder Pattern.

Complexity: CC ≤ 3 per method
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphData:
    """Immutable graph structure for plan validation."""
    
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    indegree: dict[str, int] = field(default_factory=dict)
    id_map: dict[str, Any] = field(default_factory=dict)
    
    @property
    def roots(self) -> list[str]:
        """Get root tasks (tasks with no dependencies)."""
        return [tid for tid, deg in self.indegree.items() if deg == 0]
    
    @property
    def task_count(self) -> int:
        """Get total number of tasks."""
        return len(self.id_map)
    
    @property
    def out_degrees(self) -> list[int]:
        """Get list of out-degrees for all tasks."""
        return [len(children) for children in self.adjacency.values()]


class GraphDataBuilder:
    """
    Builds graph data structures incrementally using Builder Pattern.
    
    Each method has CC ≤ 3 for maintainability.
    """
    
    def __init__(self, tasks: list[Any]):
        self.tasks = tasks
        self.adjacency: dict[str, list[str]] = {}
        self.indegree: dict[str, int] = {}
        self.id_map: dict[str, Any] = {}
        self.issues: list[Any] = []
    
    def build_id_map(self) -> "GraphDataBuilder":
        """
        Build task ID to task mapping.
        
        Complexity: CC=2
        """
        self.id_map = {t.task_id: t for t in self.tasks}
        
        if len(self.id_map) != len(self.tasks):
            from ..schemas import PlanValidationIssue
            self.issues.append(
                PlanValidationIssue(
                    code="DUPLICATE_ID",
                    message="Duplicate task_id detected"
                )
            )
        
        return self
    
    def build_adjacency(self) -> "GraphDataBuilder":
        """
        Build adjacency list (parent -> children).
        
        Complexity: CC=3
        """
        self.adjacency = {tid: [] for tid in self.id_map}
        
        for task in self.tasks:
            for dep in task.dependencies:
                if dep in self.id_map:
                    self.adjacency[dep].append(task.task_id)
                else:
                    from ..schemas import PlanValidationIssue
                    self.issues.append(
                        PlanValidationIssue(
                            code="INVALID_DEPENDENCY",
                            message=f"Task '{task.task_id}' depends on unknown '{dep}'",
                            task_id=task.task_id,
                        )
                    )
        
        return self
    
    def build_indegree(self) -> "GraphDataBuilder":
        """
        Build indegree map (task -> number of dependencies).
        
        Complexity: CC=3
        """
        self.indegree = {tid: 0 for tid in self.id_map}
        
        for task in self.tasks:
            for dep in task.dependencies:
                if dep in self.id_map:
                    self.indegree[task.task_id] += 1
        
        return self
    
    def build(self) -> tuple[GraphData, list[Any]]:
        """
        Build final GraphData object.
        
        Complexity: CC=1
        Returns: (GraphData, list of issues)
        """
        graph_data = GraphData(
            adjacency=self.adjacency,
            indegree=self.indegree,
            id_map=self.id_map,
        )
        return graph_data, self.issues
