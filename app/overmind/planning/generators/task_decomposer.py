# app/overmind/planning/generators/task_decomposer.py
"""Task decomposer with CC ≤ 4."""

from dataclasses import dataclass
from typing import Any

from .objective_analyzer import AnalyzedObjective, ComplexityLevel
from .context_enricher import EnrichedContext


@dataclass
class Task:
    """Simple task representation."""
    task_id: str
    description: str
    dependencies: list[str]
    priority: int = 100
    estimated_effort: int = 1


class TaskDecomposer:
    """Decomposes objectives into tasks. CC ≤ 4"""
    
    def decompose(
        self, objective: AnalyzedObjective, context: EnrichedContext
    ) -> list[Task]:
        """Decompose objective into tasks. CC=4"""
        if objective.complexity == ComplexityLevel.LOW:
            return self._decompose_simple(objective)
        elif objective.complexity == ComplexityLevel.MEDIUM:
            return self._decompose_medium(objective)
        else:
            return self._decompose_complex(objective, context)
    
    def _decompose_simple(self, objective: AnalyzedObjective) -> list[Task]:
        """Decompose simple objective. CC=2"""
        tasks = []
        
        for i in range(min(objective.estimated_tasks, 5)):
            tasks.append(Task(
                task_id=f"task_{i+1}",
                description=f"Step {i+1} for: {objective.original[:50]}",
                dependencies=[f"task_{i}"] if i > 0 else [],
                priority=100 - i * 10,
            ))
        
        return tasks
    
    def _decompose_medium(self, objective: AnalyzedObjective) -> list[Task]:
        """Decompose medium objective. CC=2"""
        tasks = []
        
        for i in range(min(objective.estimated_tasks, 10)):
            tasks.append(Task(
                task_id=f"task_{i+1}",
                description=f"Step {i+1} for: {objective.original[:50]}",
                dependencies=self._calculate_dependencies(i),
                priority=100 - i * 5,
                estimated_effort=2,
            ))
        
        return tasks
    
    def _decompose_complex(
        self, objective: AnalyzedObjective, context: EnrichedContext
    ) -> list[Task]:
        """Decompose complex objective. CC=3"""
        tasks = []
        
        num_tasks = min(objective.estimated_tasks, 20)
        
        for i in range(num_tasks):
            tasks.append(Task(
                task_id=f"task_{i+1}",
                description=f"Step {i+1} for: {objective.original[:50]}",
                dependencies=self._calculate_dependencies(i),
                priority=self._calculate_priority(i, num_tasks),
                estimated_effort=3,
            ))
        
        return tasks
    
    def _calculate_dependencies(self, index: int) -> list[str]:
        """Calculate task dependencies. CC=2"""
        if index == 0:
            return []
        elif index == 1:
            return ["task_1"]
        else:
            return [f"task_{index}"]
    
    def _calculate_priority(self, index: int, total: int) -> int:
        """Calculate task priority. CC=2"""
        base_priority = 100
        decrement = (100 // total) if total > 0 else 10
        return max(0, base_priority - index * decrement)
