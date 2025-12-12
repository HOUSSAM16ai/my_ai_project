"""
Task Executor Adapter - Infrastructure Layer
============================================
Adapter for task execution.
"""
from __future__ import annotations

from typing import Any


class TaskExecutorAdapter:
    """Adapter for executing tasks."""

    def __init__(self, generation_manager):
        """
        Initialize with generation manager reference.
        
        Args:
            generation_manager: Reference to generation manager
        """
        self.generation_manager = generation_manager

    def execute(self, task: Any, model: str | None = None) -> None:
        """
        Execute task using TaskExecutor.
        
        Args:
            task: Task to execute
            model: Optional model override
        """
        from app.services.task_executor_refactored import TaskExecutor

        executor = TaskExecutor(self.generation_manager)
        executor.execute(task, model)


__all__ = ["TaskExecutorAdapter"]
