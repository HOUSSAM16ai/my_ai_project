# app/services/overmind/domain/cognitive.py
"""
الدماغ الخارق (SuperBrain) - المجال المعرفي للعقل المدبر.
---------------------------------------------------------
يحدد هذا الملف البنية المعرفية عالية المستوى للوكيل الخارق.
يقوم بتنسيق "مجلس الحكمة" (Strategist, Architect, Auditor, Operator)
لحل المشكلات المعقدة باستقلالية تامة وتصحيح ذاتي.

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
- استخدام بروتوكولات صارمة.
- MIT 6.0001: التجريد والخوارزميات (Abstraction & Algorithms).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar

from pydantic import BaseModel, Field

from app.core.domain.mission import Mission
from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.domain.enums import CognitiveEvent, CognitivePhase, OvermindMessage
from app.services.overmind.domain.exceptions import StalemateError

logger = logging.getLogger(__name__)

# تعريف نوع عام للنتيجة
T = TypeVar("T")


# بروتوكول استدعاء تسجيل الأحداث
class EventLogger(Protocol):
    async def __call__(self, event_type: str, payload: dict[str, object]) -> None: ...


class CognitiveCritique(BaseModel):
    """
    نموذج نتيجة المراجعة والتدقيق.
    """

    approved: bool = Field(..., description="هل تمت الموافقة على العمل؟")
    feedback: str = Field(..., description="ملاحظات المراجعة أو أسباب الرفض")
    score: float = Field(0.0, description="درجة الجودة من 0 إلى 1")


class CognitiveState(BaseModel):
    """
    يحتفظ بالحالة المعرفية الحالية للمهمة.
    """

    mission_id: int
    objective: str
    plan: dict[str, object] | None = None
    design: dict[str, object] | None = None
    execution_result: dict[str, object] | None = None
    critique: CognitiveCritique | None = None
    iteration_count: int = Field(0, description="عدد المحاولات الحالية")
    max_iterations: int = Field(5, description="الحد الأقصى لمحاولات التصحيح الذاتي")
    current_phase: CognitivePhase = CognitivePhase.PLANNING

    # الذاكرة التجميعية (Cumulative Memory) لمنع الحلقات المفرغة
    history_hashes: list[str] = Field(default_factory=list, description="سجل بصمات الخطط السابقة")


class SuperBrain:
    """
    المعالج المعرفي المركزي (The Central Cognitive Processor).

    ينسق الوكلاء في حلقة "مجلس الحكمة":
    1. الاستراتيجي (Strategist): "ماذا يجب أن نفعل؟" (تخطيط).
    2. المعماري (Architect): "كيف يجب أن ننفذ؟" (تصميم تقني).
    3. المدقق (Auditor): "هل هذا آمن وصحيح؟" (مراجعة قبل/بعد).
    4. المنفذ (Operator): "نَفِّذ." (تنفيذ فعلي).
    """

    def __init__(
        self,
        strategist: AgentPlanner,
        architect: AgentArchitect,
        operator: AgentExecutor,
        auditor: AgentReflector,
    ) -> None:
        self.strategist = strategist
        self.architect = architect
        self.operator = operator
        self.auditor = auditor

    async def _create_safe_logger(
        self, log_event: Callable[[str, dict[str, object]], Awaitable[None]] | None
    ) -> Callable[[str, dict[str, object]], Awaitable[None]]:
        """
        إنشاء دالة تسجيل آمنة.

        Args:
            log_event: دالة التسجيل الاختيارية

        Returns:
            دالة تسجيل آمنة
        """

        async def safe_log(evt_type: str, data: dict[str, object]) -> None:
            if log_event:
                await log_event(evt_type, data)

        return safe_log

    async def _handle_planning_phase(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> CognitiveCritique:
        """
        معالجة مرحلة التخطيط والمراجعة.

        Args:
            state: حالة المهمة المعرفية
            collab_context: سياق التعاون
            safe_log: دالة التسجيل الآمنة

        Returns:
            نتيجة المراجعة

        Raises:
            RuntimeError: في حال مشاكل في خدمة الذكاء الاصطناعي
        """
        # طلب خطة جديدة
        state.plan = await self._execute_phase(
            phase_name=CognitivePhase.PLANNING,
            agent_name="Strategist",
            action=lambda: self.strategist.create_plan(state.objective, collab_context),
            timeout=120.0,
            log_func=safe_log,
        )

        # الكشف عن الحلقات المفرغة (Loop Detection)
        await self._detect_and_handle_stalemate(state, collab_context, safe_log)

        # مراجعة الخطة (Auditor)
        raw_critique = await self._execute_phase(
            phase_name=CognitivePhase.REVIEW_PLAN,
            agent_name="Auditor",
            action=lambda: self.auditor.review_work(
                state.plan, f"Plan for: {state.objective}", collab_context
            ),
            timeout=60.0,
            log_func=safe_log,
        )

        critique = CognitiveCritique(
            approved=raw_critique.get("approved", False),
            feedback=raw_critique.get("feedback", "No feedback provided"),
            score=raw_critique.get("score", 0.0),
        )

        if not critique.approved:
            await safe_log(CognitiveEvent.PLAN_REJECTED, {"critique": critique.model_dump()})
            # التحقق من أخطاء التكوين
            if "OPENROUTER_API_KEY" in critique.feedback:
                raise RuntimeError(OvermindMessage.AI_SERVICE_UNAVAILABLE)
        else:
            await safe_log(CognitiveEvent.PLAN_APPROVED, {"critique": critique.model_dump()})

        return critique

    async def _detect_and_handle_stalemate(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> None:
        """
        الكشف عن الحلقات المفرغة ومعالجتها.

        Args:
            state: حالة المهمة المعرفية
            collab_context: سياق التعاون
            safe_log: دالة التسجيل الآمنة

        Raises:
            StalemateError: عند اكتشاف حلقة مفرغة
        """
        try:
            if hasattr(self.auditor, "detect_loop"):
                self.auditor.detect_loop(state.history_hashes, state.plan)

            # إضافة بصمة الخطة الحالية للتاريخ
            if hasattr(self.auditor, "_compute_hash"):
                state.history_hashes.append(self.auditor._compute_hash(state.plan))

        except StalemateError as e:
            logger.warning(f"Stalemate detected: {e}")
            await safe_log("stalemate_detected", {"reason": str(e)})

            # استراتيجية كسر الجمود
            collab_context.update(
                "system_override",
                "Warning: You are repeating failed plans. CHANGE STRATEGY IMMEDIATELY. "
                "Do not use the same tools or logic.",
            )
            # إعادة رفع الخطأ للمعالجة في المستوى الأعلى
            raise

    async def _execute_design_phase(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> None:
        """
        تنفيذ مرحلة التصميم.

        Args:
            state: حالة المهمة المعرفية
            collab_context: سياق التعاون
            safe_log: دالة التسجيل الآمنة
        """
        state.design = await self._execute_phase(
            phase_name=CognitivePhase.DESIGN,
            agent_name="Architect",
            action=lambda: self.architect.design_solution(state.plan, collab_context),
            timeout=120.0,
            log_func=safe_log,
        )

    async def _execute_execution_phase(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> None:
        """
        تنفيذ مرحلة التنفيذ.

        Args:
            state: حالة المهمة المعرفية
            collab_context: سياق التعاون
            safe_log: دالة التسجيل الآمنة
        """
        state.execution_result = await self._execute_phase(
            phase_name=CognitivePhase.EXECUTION,
            agent_name="Operator",
            action=lambda: self.operator.execute_tasks(state.design, collab_context),
            timeout=300.0,
            log_func=safe_log,
        )

    async def _execute_reflection_phase(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> None:
        """
        تنفيذ مرحلة الانعكاس والمراجعة النهائية.

        Args:
            state: حالة المهمة المعرفية
            collab_context: سياق التعاون
            safe_log: دالة التسجيل الآمنة
        """
        raw_final_critique = await self._execute_phase(
            phase_name=CognitivePhase.REFLECTION,
            agent_name="Auditor",
            action=lambda: self.auditor.review_work(
                state.execution_result, state.objective, collab_context
            ),
            timeout=60.0,
            log_func=safe_log,
        )

        state.critique = CognitiveCritique(
            approved=raw_final_critique.get("approved", False),
            feedback=raw_final_critique.get("feedback", "No feedback provided"),
            score=raw_final_critique.get("score", 0.0),
        )

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
        collab_context = InMemoryCollaborationContext(context)
        safe_log = await self._create_safe_logger(log_event)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            await safe_log(CognitiveEvent.LOOP_START, {"iteration": state.iteration_count})

            try:
                # محاولة تنفيذ دورة معرفية كاملة | Try complete cognitive cycle
                result = await self._execute_cognitive_cycle(state, collab_context, safe_log)

                if result is not None:
                    return result

            except StalemateError as se:
                self._handle_stalemate(se, state, collab_context, safe_log)

            except Exception as e:
                await self._handle_phase_error(e, state, safe_log)

        # فشل نهائي | Final failure
        raise RuntimeError(f"Mission failed after {state.max_iterations} iterations.")

    async def _execute_cognitive_cycle(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log,
    ) -> dict[str, object] | None:
        """
        تنفيذ دورة معرفية كاملة.
        Execute one complete cognitive cycle (plan → design → execute → review).

        Returns:
            dict | None: النتيجة إذا نجحت، None إذا تحتاج إعادة المحاولة
        """
        # المرحلة 1: التخطيط | Planning phase
        if not state.plan or state.current_phase == CognitivePhase.RE_PLANNING:
            planning_success = await self._try_planning_phase(state, collab_context, safe_log)
            if not planning_success:
                return None  # إعادة المحاولة

        # المرحلة 2: التصميم | Design phase
        await self._execute_design_phase(state, collab_context, safe_log)

        # المرحلة 3: التنفيذ | Execution phase
        await self._execute_execution_phase(state, collab_context, safe_log)

        # المرحلة 4: المراجعة | Review phase
        await self._execute_reflection_phase(state, collab_context, safe_log)

        # التحقق من النجاح | Check success
        if state.critique.approved:
            await safe_log(CognitiveEvent.MISSION_SUCCESS, {"result": state.execution_result})
            return state.execution_result or {}

        # إعداد للإعادة | Prepare for retry
        await self._prepare_for_retry(state, collab_context, safe_log)
        return None

    async def _try_planning_phase(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log,
    ) -> bool:
        """
        محاولة تنفيذ مرحلة التخطيط.
        Try executing planning phase with stalemate handling.

        Returns:
            bool: True إذا نجح، False إذا يحتاج إعادة
        """
        try:
            critique = await self._handle_planning_phase(state, collab_context, safe_log)

            if not critique.approved:
                state.current_phase = CognitivePhase.RE_PLANNING
                collab_context.update("feedback_from_previous_attempt", critique.feedback)
                return False

            return True

        except StalemateError:
            # استراتيجية كسر الجمود - إعادة التخطيط فوراً
            state.current_phase = CognitivePhase.RE_PLANNING
            return False

    async def _prepare_for_retry(
        self,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log,
    ) -> None:
        """
        إعداد الحالة لإعادة المحاولة.
        Prepare state for retry after failed critique.
        """
        await safe_log(
            CognitiveEvent.MISSION_CRITIQUE_FAILED, {"critique": state.critique.model_dump()}
        )
        state.current_phase = CognitivePhase.RE_PLANNING
        collab_context.update("feedback_from_execution", state.critique.feedback)

    def _handle_stalemate(
        self,
        error: StalemateError,
        state: CognitiveState,
        collab_context: InMemoryCollaborationContext,
        safe_log,
    ) -> None:
        """
        معالجة حالة الجمود.
        Handle stalemate situation by resetting context.
        """
        logger.error(f"Stalemate trapped in main loop: {error}")
        collab_context.update(
            "system_override",
            "CRITICAL: INFINITE LOOP DETECTED. TRY SOMETHING DRASTICALLY DIFFERENT.",
        )
        state.current_phase = CognitivePhase.RE_PLANNING

    async def _handle_phase_error(
        self,
        error: Exception,
        state: CognitiveState,
        safe_log,
    ) -> None:
        """
        معالجة الأخطاء في المراحل.
        Handle errors during phase execution.
        """
        logger.error(f"Error in phase {state.current_phase}: {error}")
        await safe_log(
            CognitiveEvent.PHASE_ERROR, {"phase": state.current_phase, "error": str(error)}
        )
        # Continue the loop to retry

    async def _execute_phase(
        self,
        *,
        phase_name: str,
        agent_name: str,
        action: Callable[[], Awaitable[T]],
        timeout: float,
        log_func: Callable[[str, dict[str, object]], Awaitable[None]],
    ) -> T:
        """
        منفذ المرحلة المعرفي العام (Generic Cognitive Phase Executor).

        يطبق مبدأ التجريد (Abstraction) لفصل منطق التنفيذ والمهلة الزمنية عن منطق العمل.

        Args:
            phase_name: اسم المرحلة.
            agent_name: اسم الوكيل المسؤول.
            action: الدالة المراد تنفيذها (Closure).
            timeout: المهلة الزمنية بالثواني.
            log_func: دالة التسجيل.

        Returns:
            T: نتيجة التنفيذ.

        Raises:
            RuntimeError: في حال انتهاء المهلة أو حدوث خطأ.
        """
        await log_func(CognitiveEvent.PHASE_START, {"phase": phase_name, "agent": agent_name})
        try:
            result = await asyncio.wait_for(action(), timeout=timeout)
            phase_str = str(phase_name).lower()
            await log_func(f"{phase_str}_completed", {"summary": "Phase completed successfully"})
            return result
        except TimeoutError:
            error_msg = f"{agent_name} timeout during {phase_name} (exceeded {timeout}s)"
            logger.error(error_msg)
            phase_str = str(phase_name).lower()
            await log_func(f"{phase_str}_timeout", {"error": error_msg})
            raise RuntimeError(error_msg) from None
        except Exception as e:
            raise e
