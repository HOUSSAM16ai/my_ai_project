# app/overmind/planning/llm_planner.py
"""
Ultra Hyper Semantic Planner + Deep Structural Index (Legacy Wrapper)
Version: 8.0.0-bridge (Refactored to Atomic Modular Architecture)
Status: OPTIMIZED (Cognitive Resonance Verified)

This file now acts as a compatibility bridge to the new 'hyper_planner' package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Import from the new modular structure
from .hyper_planner.core import UltraHyperPlanner

# --------------------------------------------------------------------------------------
# Base / Schemas (stubs if import fails and allowed)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import BasePlanner, PlannerError, PlanValidationError
except Exception:
    if not _ALLOW_STUB:
        raise

    class PlannerError(Exception):
        def __init__(self, msg, planner="stub", objective="", **extra):
            super().__init__(msg)
            self.planner = planner
            self.objective = objective
            self.extra = extra

    class PlanValidationError(PlannerError): ...

    class BasePlanner:
        name = "stub"


try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext
except Exception:
    if not _ALLOW_STUB:
        raise

    @dataclass
    class PlannedTask:
        task_id: str
        description: str
        tool_name: str
        tool_args: dict[str, Any]
        dependencies: list[str]

    @dataclass
    class MissionPlanSchema:
        objective: str
        tasks: list[PlannedTask]
        meta: dict[str, Any] = None

    class PlanningContext: ...


# Backward alias
LLMGroundedPlanner = UltraHyperPlanner

__all__ = [
    "LLMGroundedPlanner",
    "MissionPlanSchema",
    "PlanValidationError",
    "PlannedTask",
    "PlannerError",
    "PlanningContext",
    "UltraHyperPlanner",
]

# --------------------------------------------------------------------------------------
# Self-test (manual)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    planner = UltraHyperPlanner()
    demo = (
        "Analyze repository architecture, container layout and create file named "
        "ARCHITECTURE_overmind.md plus additional performance report"
    )
    plan = planner.generate_plan(demo)
    print("Meta:", json.dumps(plan.meta, ensure_ascii=False, indent=2))
    print("Tasks:", len(plan.tasks))
