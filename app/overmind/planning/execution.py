# app/overmind/planning/execution.py
"""
Execution engine for Planners.
Handles timeouts, thread management, and async execution wrappers.
"""
from __future__ import annotations

import asyncio
import queue
import threading
from typing import Callable, Any, TypeVar

from .schemas import MissionPlanSchema, PlanningContext
from .exceptions import PlannerTimeoutError, PlannerError, PlanValidationError

T = TypeVar("T")

def run_with_timeout_sync(
    func: Callable[..., MissionPlanSchema],
    args: tuple,
    planner_name: str,
    objective: str,
    timeout: float
) -> MissionPlanSchema:
    """
    Executes a sync planner function in a separate thread with a timeout.
    """
    container: dict[str, BaseException | MissionPlanSchema] = {}
    q: queue.Queue[int] = queue.Queue()

    def runner():
        try:
            container["result"] = func(*args)
        except BaseException as e:
            container["error"] = e
        finally:
            q.put(1)

    th = threading.Thread(target=runner, daemon=True)
    th.start()
    try:
        q.get(timeout=timeout)
    except queue.Empty as exc:
        raise PlannerTimeoutError(
            f"Timeout {timeout:.2f}s exceeded.", planner_name, objective
        ) from exc

    if "error" in container:
        err = container["error"]
        if isinstance(err, PlannerError):
            raise err
        raise PlannerError(str(err), planner_name, objective) from err

    result = container.get("result")
    _validate_result_type(result, planner_name, objective)
    return result

async def run_with_timeout_async(
    awaitable,
    planner_name: str,
    objective: str,
    timeout: float
) -> MissionPlanSchema:
    """
    Executes an async planner function with a timeout.
    """
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError as exc:
        raise PlannerTimeoutError(
            f"Async timeout {timeout:.2f}s exceeded.", planner_name, objective
        ) from exc

def _validate_result_type(result: Any, planner_name: str, objective: str):
    """Ensures the result matches the canonical schema."""
    if not isinstance(result, MissionPlanSchema):
        if hasattr(result, "objective") and hasattr(result, "tasks"):
            raise PlannerError(
                "Planner returned non-canonical MissionPlanSchema (duck-type detected). "
                "Ensure canonical schema usage.",
                planner_name,
                objective,
            )
        raise PlannerError("Planner returned invalid result type.", planner_name, objective)
