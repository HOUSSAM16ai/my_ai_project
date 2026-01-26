"""
Cognitive Phases Strategies.
----------------------------
Implements the Strategy Pattern for different cognitive phases.
Each phase is responsible for its own execution logic, interacting with specific agents.
"""

import logging
from abc import ABC, abstractmethod

from app.core.protocols import (
    AgentArchitect,
    AgentExecutor,
    AgentPlanner,
    AgentReflector,
)
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.domain.council_session import CouncilSession
from app.services.overmind.domain.enums import CognitiveEvent, CognitivePhase as PhaseEnum, OvermindMessage
from app.services.overmind.domain.exceptions import StalemateError
from app.services.overmind.domain.phase_runner import CognitivePhaseRunner
from app.services.overmind.domain.primitives import CognitiveCritique, CognitiveState, EventLogger

logger = logging.getLogger(__name__)


class CognitivePhaseStrategy(ABC):
    """
    Abstract base class for cognitive phase strategies.
    """

    def __init__(self, runner: CognitivePhaseRunner) -> None:
        self.runner = runner

    @abstractmethod
    async def execute(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> CognitiveCritique | None:
        """
        Execute the phase logic.
        """
        ...

    def _summarize_keys(self, payload: dict[str, object] | None) -> list[str]:
        """Helper to summarize keys safely."""
        return list(payload.keys()) if isinstance(payload, dict) else []


class PlanningPhase(CognitivePhaseStrategy):
    """
    Handles the Planning Phase: Strategist creates plan -> Auditor reviews plan.
    """

    def __init__(
        self,
        runner: CognitivePhaseRunner,
        strategist: AgentPlanner,
        auditor: AgentReflector,
    ) -> None:
        super().__init__(runner)
        self.strategist = strategist
        self.auditor = auditor

    async def execute(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> CognitiveCritique:
        """
        Executes planning and review. Returns the critique.
        """
        # 1. Create Plan
        state.plan = await self.runner.execute_agent_action(
            phase_name=PhaseEnum.PLANNING,
            agent_name="Strategist",
            action=lambda: self.strategist.create_plan(state.objective, collab_context),
            timeout=120.0,
            log_func=safe_log,
            session=session,
            input_data={"objective": state.objective},
            collab_context=collab_context,
        )

        # 2. Detect Loops
        await self._detect_and_handle_stalemate(state, collab_context, safe_log, session)

        # 3. Review Plan
        raw_critique = await self.runner.execute_agent_action(
            phase_name=PhaseEnum.REVIEW_PLAN,
            agent_name="Auditor",
            action=lambda: self.auditor.review_work(
                state.plan, f"Plan for: {state.objective}", collab_context
            ),
            timeout=60.0,
            log_func=safe_log,
            session=session,
            input_data={"plan_keys": self._summarize_keys(state.plan)},
            collab_context=collab_context,
        )

        critique = CognitiveCritique(
            approved=raw_critique.get("approved", False),
            feedback=raw_critique.get("feedback", "No feedback provided"),
            score=raw_critique.get("score", 0.0),
        )

        if not critique.approved:
            await safe_log(CognitiveEvent.PLAN_REJECTED, {"critique": critique.model_dump()})
            if "OPENROUTER_API_KEY" in critique.feedback:
                raise RuntimeError(OvermindMessage.AI_SERVICE_UNAVAILABLE)
        else:
            await safe_log(CognitiveEvent.PLAN_APPROVED, {"critique": critique.model_dump()})

        return critique

    async def _detect_and_handle_stalemate(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        """
        Detects infinite loops in planning.
        """
        try:
            if hasattr(self.auditor, "detect_loop"):
                self.auditor.detect_loop(state.history_hashes, state.plan)

            if hasattr(self.auditor, "_compute_hash"):
                state.history_hashes.append(self.auditor._compute_hash(state.plan))

        except StalemateError as e:
            logger.warning(f"Stalemate detected: {e}")
            await safe_log("stalemate_detected", {"reason": str(e)})

            collab_context.update(
                "system_override",
                "Warning: You are repeating failed plans. CHANGE STRATEGY IMMEDIATELY. "
                "Do not use the same tools or logic.",
            )
            if session:
                session.notify_agent(
                    "strategist",
                    {
                        "type": "stalemate_detected",
                        "reason": str(e),
                        "guidance": "Change strategy immediately.",
                    },
                )
            raise


class DesignPhase(CognitivePhaseStrategy):
    """
    Handles the Design Phase: Architect designs solution based on plan.
    """

    def __init__(
        self,
        runner: CognitivePhaseRunner,
        architect: AgentArchitect,
    ) -> None:
        super().__init__(runner)
        self.architect = architect

    async def execute(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        state.design = await self.runner.execute_agent_action(
            phase_name=PhaseEnum.DESIGN,
            agent_name="Architect",
            action=lambda: self.architect.design_solution(state.plan, collab_context),
            timeout=120.0,
            log_func=safe_log,
            session=session,
            input_data={"plan_keys": self._summarize_keys(state.plan)},
            collab_context=collab_context,
        )


class ExecutionPhase(CognitivePhaseStrategy):
    """
    Handles the Execution Phase: Operator executes the design.
    """

    def __init__(
        self,
        runner: CognitivePhaseRunner,
        operator: AgentExecutor,
    ) -> None:
        super().__init__(runner)
        self.operator = operator

    async def execute(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        state.execution_result = await self.runner.execute_agent_action(
            phase_name=PhaseEnum.EXECUTION,
            agent_name="Operator",
            action=lambda: self.operator.execute_tasks(state.design, collab_context),
            timeout=300.0,
            log_func=safe_log,
            session=session,
            input_data={"design_keys": self._summarize_keys(state.design)},
            collab_context=collab_context,
        )


class ReflectionPhase(CognitivePhaseStrategy):
    """
    Handles the Reflection Phase: Auditor reviews the final result.
    """

    def __init__(
        self,
        runner: CognitivePhaseRunner,
        auditor: AgentReflector,
    ) -> None:
        super().__init__(runner)
        self.auditor = auditor

    async def execute(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        raw_final_critique = await self.runner.execute_agent_action(
            phase_name=PhaseEnum.REFLECTION,
            agent_name="Auditor",
            action=lambda: self.auditor.review_work(
                state.execution_result, state.objective, collab_context
            ),
            timeout=60.0,
            log_func=safe_log,
            session=session,
            input_data={"execution_keys": self._summarize_keys(state.execution_result)},
            collab_context=collab_context,
        )

        state.critique = CognitiveCritique(
            approved=raw_final_critique.get("approved", False),
            feedback=raw_final_critique.get("feedback", "No feedback provided"),
            score=raw_final_critique.get("score", 0.0),
        )
