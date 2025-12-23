"""
SuperBrain (الدماغ الخارق) - The Cognitive Domain of Overmind.

This module defines the high-level cognitive architecture for the Super Agent.
It orchestrates the 'Council of Wisdom' (Strategist, Architect, Auditor, Operator)
to solve complex problems with 100% autonomy and self-correction.
"""
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from app.core.protocols import AgentPlanner, AgentArchitect, AgentExecutor, AgentReflector
from app.models import Mission, MissionStatus

class CognitiveState(BaseModel):
    """Holds the current cognitive state of the mission."""
    mission_id: int
    objective: str
    plan: Dict[str, Any] | None = None
    design: Dict[str, Any] | None = None
    execution_result: Dict[str, Any] | None = None
    critique: Dict[str, Any] | None = None
    iteration_count: int = 0
    max_iterations: int = 5
    current_phase: str = "PLANNING"

class SuperBrain:
    """
    The Central Cognitive Processor.

    Coordinates the agents in a 'Council of Wisdom' loop:
    1. Strategist (Planner): "What should we do?" (Tree of Thoughts)
    2. Architect (Designer): "How should we do it?" (Technical Spec)
    3. Auditor (Reflector): "Is this safe/correct?" (Pre-execution review)
    4. Operator (Executor): "Do it." (Action)
    5. Auditor (Reflector): "Did it work?" (Post-execution review)
    """

    def __init__(
        self,
        strategist: AgentPlanner,
        architect: AgentArchitect,
        operator: AgentExecutor,
        auditor: AgentReflector,
    ):
        self.strategist = strategist
        self.architect = architect
        self.operator = operator
        self.auditor = auditor

    async def process_mission(self, mission: Mission, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Executes the full cognitive loop for a mission.
        Returns the final result or raises an exception.
        """
        state = CognitiveState(mission_id=mission.id, objective=mission.objective)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1

            # --- Phase 1: Planning (Strategist) ---
            if not state.plan or state.current_phase == "RE-PLANNING":
                state.plan = await self.strategist.create_plan(state.objective, context or {})
                # Critique the plan
                critique = await self.auditor.review_work(state.plan, f"Plan for: {state.objective}")
                if not critique.get("approved"):
                    # Self-Correction Loop
                    continue

            # --- Phase 2: Design (Architect) ---
            state.design = await self.architect.design_solution(state.plan)

            # --- Phase 3: Execution (Operator) ---
            state.execution_result = await self.operator.execute_tasks(state.design)

            # --- Phase 4: Reflection (Auditor) ---
            state.critique = await self.auditor.review_work(state.execution_result, state.objective)

            if state.critique.get("approved"):
                return state.execution_result
            else:
                # Feedback loop: Adjust plan or design based on critique
                state.current_phase = "RE-PLANNING"
                # In a real system, we'd inject the critique into the context for the next loop
                if context:
                    context["feedback"] = state.critique.get("feedback")

        raise RuntimeError(f"Mission failed after {state.max_iterations} iterations of the Council of Wisdom.")
