# app/services/overmind/domain/cognitive.py
"""
الدماغ الخارق (SuperBrain) - المجال المعرفي للعقل المدبر.
---------------------------------------------------------
يحدد هذا الملف البنية المعرفية عالية المستوى للوكيل الخارق.
يقوم بتنسيق "مجلس الحكمة" باستخدام نمط الاستراتيجية (Strategy Pattern)
لحل المشكلات المعقدة باستقلالية تامة وتصحيح ذاتي.

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
- استخدام بروتوكولات صارمة.
- MIT 6.0001: التجريد والخوارزميات (Abstraction & Algorithms).
"""

import logging
from collections.abc import Awaitable, Callable

from app.core.domain.mission import Mission
from app.core.protocols import (
    AgentArchitect,
    AgentExecutor,
    AgentMemory,
    AgentPlanner,
    AgentReflector,
)
from app.services.overmind.collaboration import CollaborationHub
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.domain.council_session import CouncilSession
from app.services.overmind.domain.enums import CognitiveEvent, CognitivePhase
from app.services.overmind.domain.exceptions import StalemateError
from app.services.overmind.domain.phase_runner import CognitivePhaseRunner
from app.services.overmind.domain.phases import (
    DesignPhase,
    ExecutionPhase,
    PlanningPhase,
    ReflectionPhase,
)
from app.services.overmind.domain.primitives import (
    CognitiveState,
    EventLogger,
)

logger = logging.getLogger(__name__)


class SuperBrain:
    """
    المعالج المعرفي المركزي (The Central Cognitive Processor).

    ينسق الوكلاء في حلقة "مجلس الحكمة" باستخدام استراتيجيات محددة لكل مرحلة:
    1. الاستراتيجي (Strategist): تخطيط.
    2. المعماري (Architect): تصميم.
    3. المنفذ (Operator): تنفيذ.
    4. المدقق (Auditor): مراجعة.
    """

    def __init__(
        self,
        strategist: AgentPlanner,
        architect: AgentArchitect,
        operator: AgentExecutor,
        auditor: AgentReflector,
        collaboration_hub: CollaborationHub | None = None,
        memory_agent: AgentMemory | None = None,
    ) -> None:
        self.collaboration_hub = collaboration_hub

        # تهيئة المشغل والاستراتيجيات
        self.runner = CognitivePhaseRunner(memory_agent)

        self.planning_phase = PlanningPhase(strategist, auditor)
        self.design_phase = DesignPhase(architect)
        self.execution_phase = ExecutionPhase(operator)
        self.reflection_phase = ReflectionPhase(auditor)

    async def process_mission(
        self,
        mission: Mission,
        *,
        context: dict[str, object] | None = None,
        log_event: Callable[[str, dict[str, object]], Awaitable[None]] | None = None,
    ) -> dict[str, object]:
        """
        تنفيذ الحلقة المعرفية الكاملة للمهمة.
        Execute complete cognitive loop for mission.

        Args:
            mission: كائن المهمة
            context: سياق إضافي
            log_event: دالة استدعاء لتسجيل الأحداث

        Returns:
            dict: النتيجة النهائية للمهمة

        Raises:
            RuntimeError: في حال فشل المهمة بعد استنفاد المحاولات
        """
        state = CognitiveState(mission_id=mission.id, objective=mission.objective)
        base_context = dict(context or {})
        base_context["mission_id"] = mission.id
        base_context["objective"] = mission.objective

        collab_context = InMemoryCollaborationContext(base_context)
        session = CouncilSession(hub=self.collaboration_hub, context=collab_context)
        safe_log = await self.runner.create_safe_logger(log_event)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            await safe_log(CognitiveEvent.LOOP_START, {"iteration": state.iteration_count})

            try:
                # محاولة تنفيذ دورة معرفية كاملة
                result = await self._execute_cognitive_cycle(
                    state, collab_context, safe_log, session
                )

                if result is not None:
                    return result

            except StalemateError as se:
                self._handle_stalemate(se, state, collab_context, safe_log, session)

            except Exception as e:
                await self._handle_phase_error(e, state, safe_log)

        # فشل نهائي
        raise RuntimeError(f"Mission failed after {state.max_iterations} iterations.")

    async def _execute_cognitive_cycle(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> dict[str, object] | None:
        """
        تنفيذ دورة معرفية كاملة.
        Execute one complete cognitive cycle (plan → design → execute → review).
        """
        # المرحلة 1: التخطيط | Planning phase
        if not state.plan or state.current_phase == CognitivePhase.RE_PLANNING:
            critique = await self.planning_phase.execute(
                state, collab_context, self.runner, session, safe_log
            )

            if not critique.approved:
                state.current_phase = CognitivePhase.RE_PLANNING
                collab_context.update("feedback_from_previous_attempt", critique.feedback)
                return None  # إعادة المحاولة

        # المرحلة 2: التصميم | Design phase
        await self.design_phase.execute(
            state, collab_context, self.runner, session, safe_log
        )

        # المرحلة 3: التنفيذ | Execution phase
        await self.execution_phase.execute(
            state, collab_context, self.runner, session, safe_log
        )

        # المرحلة 4: المراجعة | Review phase
        await self.reflection_phase.execute(
            state, collab_context, self.runner, session, safe_log
        )

        # التحقق من النجاح | Check success
        if state.critique and state.critique.approved:
            await safe_log(CognitiveEvent.MISSION_SUCCESS, {"result": state.execution_result})
            return state.execution_result or {}

        # إعداد للإعادة | Prepare for retry
        await self._prepare_for_retry(state, collab_context, safe_log, session)
        return None

    async def _prepare_for_retry(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        """
        إعداد الحالة لإعادة المحاولة.
        """
        if state.critique:
            await safe_log(
                CognitiveEvent.MISSION_CRITIQUE_FAILED, {"critique": state.critique.model_dump()}
            )
            state.current_phase = CognitivePhase.RE_PLANNING
            collab_context.update("feedback_from_execution", state.critique.feedback)
            if session:
                session.notify_agent(
                    "strategist",
                    {
                        "type": "critique_failed",
                        "feedback": state.critique.feedback,
                        "iteration": state.iteration_count,
                    },
                )

    def _handle_stalemate(
        self,
        error: StalemateError,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: EventLogger,
        session: CouncilSession | None,
    ) -> None:
        """
        معالجة حالة الجمود.
        """
        logger.error(f"Stalemate trapped in main loop: {error}")
        collab_context.update(
            "system_override",
            "CRITICAL: INFINITE LOOP DETECTED. TRY SOMETHING DRASTICALLY DIFFERENT.",
        )
        # Force re-planning by invalidating the current plan
        state.plan = None
        state.current_phase = CognitivePhase.RE_PLANNING
        if session:
            session.notify_agent(
                "strategist",
                {"type": "critical_stalemate", "reason": str(error)},
            )

    async def _handle_phase_error(
        self,
        error: Exception,
        state: CognitiveState,
        safe_log: EventLogger,
    ) -> None:
        """
        معالجة الأخطاء في المراحل.
        """
        logger.error(f"Error in phase {state.current_phase}: {error}")
        await safe_log(
            CognitiveEvent.PHASE_ERROR, {"phase": state.current_phase, "error": str(error)}
        )
