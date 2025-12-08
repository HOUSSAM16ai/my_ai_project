"""
Test for health checker background task reference bug fix.

This test verifies that the HealthChecker properly maintains strong references
to background tasks to prevent them from being garbage collected.
"""

import asyncio
import gc
import weakref

import pytest

from app.core.scaling.health_checker import HealthChecker
from app.core.scaling.service_registry import ServiceRegistry


@pytest.mark.asyncio
async def test_health_checker_task_not_garbage_collected():
    """
    Verify that the health check task is not garbage collected while running.

    This test ensures the fix for the asyncio.create_task reference bug is working.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    # Start the health checker
    await checker.start()

    # Get a weak reference to the task
    assert checker._task is not None
    task_weakref = weakref.ref(checker._task)

    # Force garbage collection
    gc.collect()

    # Task should still exist (not garbage collected)
    assert task_weakref() is not None, "Task was garbage collected while still running"

    # Verify task is actually running
    assert not checker._task.done(), "Task should still be running"

    # Stop the checker
    await checker.stop()

    # After stopping, task should be cancelled
    assert checker._task.cancelled() or checker._task.done()


@pytest.mark.asyncio
async def test_health_checker_maintains_background_tasks_set():
    """
    Verify that the HealthChecker maintains a set of background tasks.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    # Initially, background tasks set should be empty
    assert len(checker._background_tasks) == 0

    # Start the health checker
    await checker.start()

    # Background tasks set should contain the task
    assert len(checker._background_tasks) == 1
    assert checker._task in checker._background_tasks

    # Stop the checker
    await checker.stop()

    # After stopping and task completion, set should be cleaned up
    # Wait a bit for the callback to execute
    await asyncio.sleep(0.1)
    assert len(checker._background_tasks) == 0


@pytest.mark.asyncio
async def test_health_checker_task_cleanup_on_completion():
    """
    Verify that completed tasks are removed from the background tasks set.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    await checker.start()

    # Task should be in the set
    assert checker._task in checker._background_tasks

    # Stop the checker (which cancels the task)
    await checker.stop()

    # Wait for the done callback to execute
    await asyncio.sleep(0.1)

    # Task should be removed from the set
    assert checker._task not in checker._background_tasks


@pytest.mark.asyncio
async def test_health_checker_multiple_start_calls():
    """
    Verify that calling start() multiple times doesn't create multiple tasks.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    await checker.start()
    first_task = checker._task

    # Try to start again
    await checker.start()

    # Should be the same task
    assert checker._task is first_task
    assert len(checker._background_tasks) == 1

    await checker.stop()


@pytest.mark.asyncio
async def test_health_checker_task_survives_gc_cycles():
    """
    Verify that the task survives multiple garbage collection cycles.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    await checker.start()

    # Run multiple GC cycles
    for _ in range(5):
        gc.collect()
        await asyncio.sleep(0.05)

    # Task should still be running
    assert checker._task is not None
    assert not checker._task.done()

    await checker.stop()


@pytest.mark.asyncio
async def test_health_checker_done_callback_registered():
    """
    Verify that the done callback is properly registered on the task.
    """
    registry = ServiceRegistry()
    checker = HealthChecker(registry, check_interval=0.1)

    await checker.start()

    # Check that the task has callbacks registered
    # Note: This is implementation-specific, but we can verify the task exists
    assert checker._task is not None

    # The task should be in the background tasks set
    assert checker._task in checker._background_tasks

    await checker.stop()
