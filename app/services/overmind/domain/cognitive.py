"""
SuperBrain (الدماغ الخارق) - The Cognitive Domain of Overmind.

This module defines the high-level cognitive architecture for the Super Agent.
It orchestrates the 'Council of Wisdom' (Strategist, Architect, Auditor, Operator)
to solve complex problems with 100% autonomy and self-correction.
"""
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from pydantic import BaseModel

from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.models import Mission


# Callback protocol for event logging
class EventLogger(Protocol):
    async def __call__(self, event_type: str, payload: dict[str, Any]) -> None: ...

class CognitiveState(BaseModel):
    """Holds the current cognitive state of the mission."""
    mission_id: int
    objective: str
    plan: dict[str, Any] | None = None
    design: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    critique: dict[str, Any] | None = None
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

    async def process_mission(
        self,
        mission: Mission,
        context: dict[str, Any] | None = None,
        log_event: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None
    ) -> dict[str, Any]:
        """
        Executes the full cognitive loop for a mission.
        Returns the final result or raises an exception.

        Args:
            mission: The mission object.
            context: Optional context dictionary.
            log_event: Async callback to log events to the state manager.
        """
        state = CognitiveState(mission_id=mission.id, objective=mission.objective)

        async def safe_log(evt_type: str, data: dict[str, Any]):
            if log_event:
                await log_event(evt_type, data)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            await safe_log("loop_start", {"iteration": state.iteration_count})

            # --- Phase 1: Planning (Strategist) ---
            if not state.plan or state.current_phase == "RE-PLANNING":
                await safe_log("phase_start", {"phase": "PLANNING", "agent": "Strategist"})
                state.plan = await self.strategist.create_plan(state.objective, context or {})
                await safe_log("plan_created", {"plan_summary": "Plan created successfully"})

                # Critique the plan
                await safe_log("phase_start", {"phase": "REVIEW_PLAN", "agent": "Auditor"})
                critique = await self.auditor.review_work(state.plan, f"Plan for: {state.objective}")
                if not critique.get("approved"):
                    await safe_log("plan_rejected", {"critique": critique})
                    # Self-Correction Loop
                    state.current_phase = "RE-PLANNING"
                    continue
                await safe_log("plan_approved", {"critique": critique})

            # --- Phase 2: Design (Architect) ---
            await safe_log("phase_start", {"phase": "DESIGN", "agent": "Architect"})
            state.design = await self.architect.design_solution(state.plan)
            await safe_log("design_created", {"design_summary": "Design spec created"})

            # --- Phase 3: Execution (Operator) ---
            await safe_log("phase_start", {"phase": "EXECUTION", "agent": "Operator"})
            # Note: Executor should ideally report progress too, but we wait for result here
            state.execution_result = await self.operator.execute_tasks(state.design)
            await safe_log("execution_completed", {"status": "done"})

            # --- Phase 4: Reflection (Auditor) ---
            await safe_log("phase_start", {"phase": "REFLECTION", "agent": "Auditor"})
            state.critique = await self.auditor.review_work(state.execution_result, state.objective)

            if state.critique.get("approved"):
                await safe_log("mission_success", {"result": state.execution_result})
                return state.execution_result
            await safe_log("mission_critique_failed", {"critique": state.critique})
            # Feedback loop: Adjust plan or design based on critique
            state.current_phase = "RE-PLANNING"
            # In a real system, we'd inject the critique into the context for the next loop
            if context:
                context["feedback"] = state.critique.get("feedback")

        error_msg = f"Mission failed after {state.max_iterations} iterations of the Council of Wisdom."
        await safe_log("mission_failed", {"reason": "max_iterations_exceeded"})
        raise RuntimeError(error_msg)
