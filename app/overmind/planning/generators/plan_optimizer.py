# app/overmind/planning/generators/plan_optimizer.py
"""Plan optimizer with CC ≤ 3."""

from typing import Any


class PlanOptimizer:
    """Optimizes plan structure. CC ≤ 3"""

    def optimize(self, tasks: list[Any], graph: Any) -> list[Any]:
        """Optimize task order and priorities. CC=3"""
        if not tasks:
            return tasks

        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Rebalance priorities
        rebalanced = self._rebalance_priorities(sorted_tasks)

        return rebalanced

    def _rebalance_priorities(self, tasks: list[Any]) -> list[Any]:
        """Rebalance task priorities. CC=2"""
        if len(tasks) <= 1:
            return tasks

        step = 100 // len(tasks) if len(tasks) > 0 else 10

        for i, task in enumerate(tasks):
            task.priority = 100 - i * step

        return tasks
