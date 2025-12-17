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
        Execute task (stub implementation).

        Note: Task execution has been moved to overmind/executor.py.
        This adapter is kept for backward compatibility but does not execute tasks.

        Args:
            task: Task to execute
            model: Optional model override
        """
        raise NotImplementedError(
            "Task execution has been moved to app.services.overmind.executor.TaskExecutor. "
            "Use the Overmind orchestrator for task execution."
        )


__all__ = ["TaskExecutorAdapter"]
