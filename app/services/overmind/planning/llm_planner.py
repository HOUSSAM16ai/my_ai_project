# app/overmind/planning/llm_planner.py
"""
Ultra Hyper Semantic Planner + Deep Structural Index (Legacy Wrapper)
Version: 8.0.0-bridge (Refactored to Atomic Modular Architecture)
Status: OPTIMIZED (Cognitive Resonance Verified)

This file now acts as a compatibility bridge to the new 'hyper_planner' package.
"""

from __future__ import annotations

# Import from the new modular structure
from .hyper_planner.core import UltraHyperPlanner

# Import core schemas directly (No stubs allowed - Structure is strict)
from .schemas import (
    MissionPlanSchema,
    PlannedTask,
    PlannerError,
    PlanningContext,
    PlanValidationError,
)

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
    print("Meta:", json.dumps(plan.meta.model_dump() if plan.meta else {}, ensure_ascii=False, indent=2))
    print("Tasks:", len(plan.tasks))
