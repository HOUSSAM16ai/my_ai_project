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
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, Field

from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.models import Mission
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.domain.enums import CognitiveEvent, CognitivePhase, OvermindMessage

logger = logging.getLogger(__name__)

# تعريف نوع عام للنتيجة
T = TypeVar("T")

# بروتوكول استدعاء تسجيل الأحداث
class EventLogger(Protocol):
    async def __call__(self, event_type: str, payload: dict[str, Any]) -> None: ...


class CognitiveState(BaseModel):
    """
    يحتفظ بالحالة المعرفية الحالية للمهمة.
    """
    mission_id: int
    objective: str
    plan: dict[str, Any] | None = None
    design: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    critique: dict[str, Any] | None = None
    iteration_count: int = Field(0, description="عدد المحاولات الحالية")
    max_iterations: int = Field(5, description="الحد الأقصى لمحاولات التصحيح الذاتي")
    current_phase: CognitivePhase = CognitivePhase.PLANNING


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
        *,
        strategist: AgentPlanner,
        architect: AgentArchitect,
        operator: AgentExecutor,
        auditor: AgentReflector,
    ) -> None:
        self.strategist = strategist
        self.architect = architect
        self.operator = operator
        self.auditor = auditor

    async def process_mission(
        self,
        mission: Mission,
        *,
        context: dict[str, Any] | None = None,
        log_event: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None
    ) -> dict[str, Any]:
        """
        تنفيذ الحلقة المعرفية الكاملة للمهمة.

        Args:
            mission: كائن المهمة.
            context: سياق إضافي.
            log_event: دالة استدعاء لتسجيل الأحداث في الذاكرة.

        Returns:
            dict: النتيجة النهائية للمهمة.

        Raises:
            RuntimeError: في حال فشل المهمة بعد استنفاد المحاولات.
        """
        state = CognitiveState(mission_id=mission.id, objective=mission.objective)
        collab_context = InMemoryCollaborationContext(context)

        # دالة مساعدة للتسجيل الآمن
        async def safe_log(evt_type: str, data: dict[str, Any]) -> None:
            if log_event:
                await log_event(evt_type, data)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            await safe_log(CognitiveEvent.LOOP_START, {"iteration": state.iteration_count})

            try:
                # --- المرحلة 1: التخطيط (Strategist) ---
                if not state.plan or state.current_phase == CognitivePhase.RE_PLANNING:
                    state.plan = await self._execute_phase(
                        phase_name=CognitivePhase.PLANNING,
                        agent_name="Strategist",
                        action=lambda: self.strategist.create_plan(state.objective, collab_context),
                        timeout=120.0,
                        log_func=safe_log
                    )

                    # مراجعة الخطة (Auditor)
                    critique = await self._execute_phase(
                        phase_name=CognitivePhase.REVIEW_PLAN,
                        agent_name="Auditor",
                        action=lambda: self.auditor.review_work(state.plan, f"Plan for: {state.objective}", collab_context),
                        timeout=60.0,
                        log_func=safe_log
                    )

                    if not critique.get("approved"):
                        await safe_log(CognitiveEvent.PLAN_REJECTED, {"critique": critique})
                        # التحقق من أخطاء التكوين
                        feedback = critique.get("feedback", "")
                        if "OPENROUTER_API_KEY" in feedback:
                            raise RuntimeError(OvermindMessage.AI_SERVICE_UNAVAILABLE)

                        state.current_phase = CognitivePhase.RE_PLANNING
                        collab_context.update("feedback_from_previous_attempt", feedback)
                        continue # إعادة المحاولة

                    await safe_log(CognitiveEvent.PLAN_APPROVED, {"critique": critique})

                # --- المرحلة 2: التصميم (Architect) ---
                state.design = await self._execute_phase(
                    phase_name=CognitivePhase.DESIGN,
                    agent_name="Architect",
                    action=lambda: self.architect.design_solution(state.plan, collab_context),
                    timeout=120.0,
                    log_func=safe_log
                )

                # --- المرحلة 3: التنفيذ (Operator) ---
                state.execution_result = await self._execute_phase(
                    phase_name=CognitivePhase.EXECUTION,
                    agent_name="Operator",
                    action=lambda: self.operator.execute_tasks(state.design, collab_context),
                    timeout=300.0,
                    log_func=safe_log
                )

                # --- المرحلة 4: الانعكاس والمراجعة النهائية (Auditor) ---
                state.critique = await self._execute_phase(
                    phase_name=CognitivePhase.REFLECTION,
                    agent_name="Auditor",
                    action=lambda: self.auditor.review_work(state.execution_result, state.objective, collab_context),
                    timeout=60.0,
                    log_func=safe_log
                )

                if state.critique.get("approved"):
                    await safe_log(CognitiveEvent.MISSION_SUCCESS, {"result": state.execution_result})
                    return state.execution_result or {}

                await safe_log(CognitiveEvent.MISSION_CRITIQUE_FAILED, {"critique": state.critique})
                state.current_phase = CognitivePhase.RE_PLANNING
                collab_context.update("feedback_from_execution", state.critique.get("feedback"))

            except Exception as e:
                logger.error(f"Error in phase {state.current_phase}: {e}")
                await safe_log(CognitiveEvent.PHASE_ERROR, {"phase": state.current_phase, "error": str(e)})
                if isinstance(e, RuntimeError) and "timeout" in str(e).lower():
                    # Timeouts are critical, force retry or fail
                    pass
                # continue the loop to retry

        # فشل نهائي
        raise RuntimeError(f"Mission failed after {state.max_iterations} iterations.")

    async def _execute_phase(
        self,
        *,
        phase_name: str,
        agent_name: str,
        action: Callable[[], Awaitable[T]],
        timeout: float,
        log_func: Callable[[str, dict[str, Any]], Awaitable[None]]
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
            # Use string interpolation or enum value safely for logging
            phase_str = str(phase_name).lower()
            await log_func(f"{phase_str}_completed", {"summary": "Phase completed successfully"})
            return result
        except TimeoutError:
            error_msg = f"{agent_name} timeout during {phase_name} (exceeded {timeout}s)"
            logger.error(error_msg)
            phase_str = str(phase_name).lower()
            await log_func(f"{phase_str}_timeout", {"error": error_msg})
            raise RuntimeError(error_msg)
        except Exception as e:
            # إعادة رمي الاستثناء ليتم التعامل معه في الحلقة الرئيسية
            raise e
