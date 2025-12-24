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
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.models import Mission


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
    current_phase: str = "PLANNING"


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

        # تحويل القاموس الأولي إلى كائن سياق تعاوني
        collab_context = InMemoryCollaborationContext(context)

        async def safe_log(evt_type: str, data: dict[str, Any]) -> None:
            if log_event:
                await log_event(evt_type, data)

        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            await safe_log("loop_start", {"iteration": state.iteration_count})

            # --- المرحلة 1: التخطيط (Strategist) ---
            if not state.plan or state.current_phase == "RE-PLANNING":
                await safe_log("phase_start", {"phase": "PLANNING", "agent": "Strategist"})

                # الاستراتيجي يضع الخطة
                state.plan = await self.strategist.create_plan(state.objective, collab_context)
                await safe_log("plan_created", {"plan_summary": "تم إنشاء الخطة بنجاح"})

                # المدقق يراجع الخطة
                await safe_log("phase_start", {"phase": "REVIEW_PLAN", "agent": "Auditor"})
                critique = await self.auditor.review_work(state.plan, f"Plan for: {state.objective}", collab_context)

                if not critique.get("approved"):
                    await safe_log("plan_rejected", {"critique": critique})
                    # حلقة التصحيح الذاتي (Self-Correction Loop)
                    state.current_phase = "RE-PLANNING"
                    # دمج الملاحظات في السياق للمحاولة التالية
                    collab_context.update("feedback_from_previous_attempt", critique.get("feedback"))
                    continue

                await safe_log("plan_approved", {"critique": critique})

            # --- المرحلة 2: التصميم (Architect) ---
            await safe_log("phase_start", {"phase": "DESIGN", "agent": "Architect"})
            state.design = await self.architect.design_solution(state.plan, collab_context)
            await safe_log("design_created", {"design_summary": "تم وضع التصميم التقني"})

            # --- المرحلة 3: التنفيذ (Operator) ---
            await safe_log("phase_start", {"phase": "EXECUTION", "agent": "Operator"})
            # المنفذ يقوم بالعمل
            state.execution_result = await self.operator.execute_tasks(state.design, collab_context)
            await safe_log("execution_completed", {"status": "done"})

            # --- المرحلة 4: الانعكاس والمراجعة النهائية (Auditor) ---
            await safe_log("phase_start", {"phase": "REFLECTION", "agent": "Auditor"})
            state.critique = await self.auditor.review_work(state.execution_result, state.objective, collab_context)

            if state.critique.get("approved"):
                await safe_log("mission_success", {"result": state.execution_result})
                return state.execution_result

            await safe_log("mission_critique_failed", {"critique": state.critique})

            # إعادة المحاولة بناءً على التغذية الراجعة
            state.current_phase = "RE-PLANNING"
            collab_context.update("feedback_from_execution", state.critique.get("feedback"))

        # إذا وصلنا هنا، فقد فشلت المهمة بعد كل المحاولات
        error_msg = f"فشلت المهمة بعد {state.max_iterations} دورات من مجلس الحكمة."
        await safe_log("mission_failed", {"reason": "max_iterations_exceeded"})
        raise RuntimeError(error_msg)
