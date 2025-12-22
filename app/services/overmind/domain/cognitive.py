# app/services/overmind/domain/cognitive.py
# =================================================================================================
# COGNITIVE DOMAIN - THE BRAIN (الدماغ)
# Version: 1.0.0-solid
# =================================================================================================

import logging
from typing import Any
from collections.abc import Awaitable

from app.core.protocols import AgentPlanner, AgentReflector

logger = logging.getLogger(__name__)

class SuperBrain:
    """
    المنسق المعرفي (Cognitive Coordinator).
    يجمع بين التخطيط والنقد (Planning & Reflection).

    Responsibility (SRP):
    Coordination of cognitive processes. It does not execute tools; it thinks.
    """

    def __init__(self, planner: AgentPlanner, reflector: AgentReflector):
        """
        Dependency Injection (DIP):
        The brain depends on abstractions (protocols), not concrete implementations.
        """
        self.planner = planner
        self.reflector = reflector

    async def think_and_plan(self, objective: str) -> dict[str, Any]:
        """
        Generates a plan and critiques it immediately (Self-Correction).
        """
        logger.info("Brain: Generating initial plan...")
        plan = await self.planner.create_plan(objective)

        # Self-Reflection Step
        logger.info("Brain: Critiquing plan...")
        critique = await self.reflector.critique_plan(objective, plan)

        if not critique.get("approved", False):
            logger.warning(f"Brain: Plan rejected by critic. Reason: {critique.get('feedback')}")
            # In a real system, we would loop here to refine the plan based on feedback.
            # For this implementation, we mark it as 'needs_refinement' in the meta.
            plan["meta"] = plan.get("meta", {})
            plan["meta"]["critique"] = critique
            plan["meta"]["status"] = "needs_refinement"
        else:
            logger.info("Brain: Plan approved by critic.")
            plan["meta"] = plan.get("meta", {})
            plan["meta"]["status"] = "approved"

        return plan

class StandardPlanner:
    """
    A concrete implementation of AgentPlanner.
    (Simulated logic for architectural demonstration)
    """
    async def create_plan(self, objective: str) -> dict[str, Any]:
        # In a real scenario, this would call an LLM.
        return {
            "objective": objective,
            "steps": [
                {"id": 1, "action": "analyze", "description": "Analyze the request"},
                {"id": 2, "action": "execute", "description": "Execute the core logic"}
            ],
            "meta": {"source": "StandardPlanner"}
        }

class StandardReflector:
    """
    A concrete implementation of AgentReflector.
    (Simulated logic)
    """
    async def critique_plan(self, objective: str, plan: dict[str, Any]) -> dict[str, Any]:
        # Simple heuristic: If plan has steps, approve it.
        steps = plan.get("steps", [])
        if len(steps) > 0:
            return {"approved": True, "feedback": "Plan looks solid."}
        return {"approved": False, "feedback": "Plan is empty."}

    async def critique_result(self, task: Any, result: Any) -> dict[str, Any]:
        if result.get("status") == "success":
            return {"approved": True, "feedback": "Good job."}
        return {"approved": False, "feedback": "Task failed."}
