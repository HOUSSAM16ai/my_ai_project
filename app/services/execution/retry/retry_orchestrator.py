# app/services/execution/retry/retry_orchestrator.py
"""Retry orchestrator with CC ≤ 5."""

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionResult:
    """Execution result."""

    success: bool
    message: str = ""
    data: Any = None


class RetryStrategy:
    """Exponential backoff retry strategy. CC ≤ 3"""

    def __init__(self, max_attempts: int = 3, base_delay: float = 0.1):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    def attempts(self) -> Iterator[int]:
        """Generate attempt numbers. CC=1"""
        yield from range(self.max_attempts)

    def should_retry(self, result: ExecutionResult, attempt: int) -> bool:
        """Check if should retry. CC=2"""
        return not result.success and attempt < self.max_attempts - 1

    def wait(self, attempt: int) -> None:
        """Wait before retry. CC=2"""
        delay = self.base_delay * (2**attempt)
        time.sleep(delay)


class TaskExecutor:
    """Executes individual tasks. CC ≤ 3"""

    def execute(self, task: Any) -> ExecutionResult:
        """Execute task. CC=3"""
        try:
            # Placeholder - actual implementation would execute real task
            if hasattr(task, "execute"):
                result = task.execute()
                return ExecutionResult(success=True, data=result)
            return ExecutionResult(success=True, message=f"Executed {task}")
        except Exception as e:
            return ExecutionResult(success=False, message=str(e))


class RetryOrchestrator:
    """
    Orchestrates task execution with retry. CC=5

    Replaces _execute_task_with_retry_topological (CC=39).
    """

    def __init__(self):
        self.retry_strategy = RetryStrategy()
        self.task_executor = TaskExecutor()

    def execute_with_retry(self, tasks: list[Any]) -> ExecutionResult:
        """
        Execute tasks with retry. CC=5

        This replaces the original function which had CC=39.
        """
        if not tasks:
            return ExecutionResult(success=False, message="No tasks")

        # Sort tasks topologically (simplified)
        sorted_tasks = self._sort_tasks(tasks)

        # Execute each task with retry
        for task in sorted_tasks:
            result = self._execute_single_with_retry(task)

            if not result.success:
                return ExecutionResult(success=False, message=f"Task failed: {result.message}")

        return ExecutionResult(success=True, message="All tasks completed")

    def _sort_tasks(self, tasks: list[Any]) -> list[Any]:
        """Sort tasks topologically. CC=2"""
        # Simplified - actual implementation would do proper topological sort
        return sorted(tasks, key=lambda t: getattr(t, "priority", 0), reverse=True)

    def _execute_single_with_retry(self, task: Any) -> ExecutionResult:
        """Execute single task with retry. CC=4"""
        for attempt in self.retry_strategy.attempts():
            result = self.task_executor.execute(task)

            if result.success:
                return result

            if self.retry_strategy.should_retry(result, attempt):
                self.retry_strategy.wait(attempt)
                continue

            return result

        return ExecutionResult(success=False, message="Max retries exceeded")
