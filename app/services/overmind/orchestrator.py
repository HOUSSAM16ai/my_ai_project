# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE (العقل المدبر)
# Version: 14.0.0-legendary-agents
# =================================================================================================

import asyncio
import logging
from typing import Any

from app.models import Mission, MissionEventType, MissionStatus, TaskStatus
from app.services.overmind.state import MissionStateManager
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.agents import StrategistAgent, OperatorAgent, AuditorAgent
from app.core.ai_gateway import AIClient
from app.services.agent_tools.infrastructure.registry import get_registry

logger = logging.getLogger(__name__)


class OvermindOrchestrator:
    """
    العقل المدبر (Overmind Orchestrator).

    هذا الكلاس هو "الدماغ" الحقيقي للنظام. إنه المسؤول عن تحويل طلبات المستخدم المجردة
    إلى واقع ملموس عن طريق التخطيط الذكي والتنفيذ الدقيق.

    المبدأ الفلسفي: "فكر مرتين، نفذ مرة واحدة".

    كيف يعمل هذا العقل الجبار؟
    1.  **استيعاب المهمة (Understanding)**: يستلم المهمة من المستخدم ويفهم حالتها.
    2.  **التخطيط الاستراتيجي (Planning)**: يختار أفضل "مخطط" (Planner) لتقسيم المهمة المعقدة إلى خطوات صغيرة.
    3.  **التنفيذ الذكي (Execution)**: يدير تنفيذ الخطوات، ويراقب التبعيات (لا يبني السقف قبل الأعمدة!).
    4.  **المرونة (Resilience)**: يتعامل مع الأخطاء بذكاء، ويقرر متى يعيد المحاولة ومتى يعلن الفشل.

    Updates (v14):
    - Now delegates "Thinking" to the `SuperBrain` which coordinates the `Strategist`, `Operator`, and `Auditor`.
    """

    def __init__(self, state_manager: MissionStateManager, ai_client: AIClient | None = None):
        """
        تهيئة العقل المدبر.

        Args:
            state_manager: مدير الذاكرة (يحفظ حالة المهمة والخطوات).
            ai_client: بوابة الذكاء الاصطناعي (اختياري، يتم إنشاؤه تلقائياً إذا لم يمرر).
        """
        self.state = state_manager

        # Initialize the Council of Agents
        # Note: In a pure DI system, these would be injected. For now, we compose them here
        # to guarantee the "Supernatural" setup.

        # 1. AI Gateway (The Synapse)
        self._ai = ai_client # In real usage, we might instantiate a default if None

        # 2. Tool Registry (The Arsenal)
        self._registry = get_registry()

        # 3. The Agents
        self.strategist = StrategistAgent(self._ai)
        self.operator = OperatorAgent(self._registry)
        self.auditor = AuditorAgent()

        # 4. The SuperBrain (The Coordinator)
        self.brain = SuperBrain(
            planner=self.strategist,
            executor=self.operator,
            reflector=self.auditor
        )

    async def run_mission(self, mission_id: int) -> None:
        """
        نقطة الانطلاق الرئيسية للمهمة.
        Main entry point.
        """
        try:
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.error(f"Mission {mission_id} not found in memory.")
                return

            # تشغيل حلقة الحياة (The Lifecycle Loop)
            await self._run_lifecycle_loop(mission_id)

        except Exception as e:
            logger.exception(f"Fatal error in Mission {mission_id}")
            await self._handle_catastrophic_failure(mission_id, e)

    async def _run_lifecycle_loop(self, mission_id: int) -> None:
        """
        حلقة الذكاء والتنفيذ.
        The Brain Loop: Observe -> Orient -> Decide -> Act.
        """
        # إعدادات الحلقة (يمكن جعلها ديناميكية لاحقاً)
        MAX_CYCLES = 2000  # أقصى عدد دورات لتجنب الحلقات اللانهائية
        CYCLE_DELAY = 0.5  # استراحة قصيرة للتنفس (seconds)

        logger.info(f"Overmind: Starting cognitive loop for Mission {mission_id}")

        for cycle in range(MAX_CYCLES):
            # 1. الملاحظة (Observe): جلب أحدث حالة للمهمة
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.warning("Mission disappeared from memory.")
                break

            status = mission.status
            logger.debug(f"Cycle {cycle}: Mission Status = {status}")

            # 2. القرار (Decide & Act): اتخاذ إجراء بناءً على الحالة
            if status == MissionStatus.PENDING:
                # المهمة جديدة، يجب البدء بالتخطيط
                await self._phase_planning(mission)

            elif status == MissionStatus.PLANNING:
                # ننتظر انتهاء التخطيط (في حال كان غير متزامن)
                await asyncio.sleep(CYCLE_DELAY)

            elif status == MissionStatus.PLANNED:
                # الخطة جاهزة، لنبدأ التنفيذ
                await self._phase_prepare_execution(mission)

            elif status == MissionStatus.RUNNING:
                # التنفيذ جارٍ، تحقق من التقدم
                is_finished = await self._phase_execution_monitor(mission)
                if is_finished:
                    break  # انتهينا!
                await asyncio.sleep(CYCLE_DELAY)

            elif status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                # حالات النهاية
                logger.info(f"Mission {mission_id} finished with state: {status}")
                break

            else:
                # حالة غير معروفة، ننتظر قليلاً
                await asyncio.sleep(CYCLE_DELAY)

    async def _phase_planning(self, mission: Mission) -> None:
        """
        مرحلة التخطيط: تحويل الهدف إلى خطة عمل باستخدام الدماغ الخارق.
        """
        logger.info(f"Overmind: Engaging SuperBrain for Mission {mission.id}...")
        await self.state.update_mission_status(
            mission.id, MissionStatus.PLANNING, "Thinking... (Consulting Council of Agents)"
        )

        try:
            # استخدام الدماغ الخارق للتخطيط
            plan_result = await self.brain.think_and_plan(mission.objective)

            plan_schema = plan_result # The result itself is the plan dict

            # حفظ الخطة في الذاكرة
            await self.state.persist_plan(
                mission.id,
                planner_name=self.strategist.name,
                plan_schema=plan_schema,
                score=1.0, # Assumed high confidence from the council
                rationale="Ratified by Council of Agents",
            )

            # الانتقال للمرحلة التالية
            await self.state.update_mission_status(
                mission.id, MissionStatus.PLANNED, "Plan Ready. Engaging engines."
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.PLAN_SELECTED,
                {"planner": self.strategist.name},
            )

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"SuperBrain Failure: {e}"
            )

    async def _phase_prepare_execution(self, mission: Mission) -> None:
        """
        التحضير للإطلاق.
        """
        logger.info(f"Overmind: Engaging execution engines for Mission {mission.id}")
        await self.state.update_mission_status(
            mission.id, MissionStatus.RUNNING, "Execution Started"
        )
        await self.state.log_event(mission.id, MissionEventType.EXECUTION_STARTED, {})

    async def _phase_execution_monitor(self, mission: Mission) -> bool:
        """
        مراقب التنفيذ: يراقب المهام، يحدد ما هو جاهز للتنفيذ، ويعالج النتائج.
        Returns:
            True if mission is complete (Success or Fail).
            False if mission is still running.
        """
        tasks = await self.state.get_tasks(mission.id)

        # تصنيف المهام حسب حالتها
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        running_tasks = [t for t in tasks if t.status == TaskStatus.RUNNING]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]

        # 1. التحقق من شروط النهاية (Terminal Conditions)
        if not pending_tasks and not running_tasks:
            if failed_tasks:
                # انتهت كل المهام وهناك فشل
                await self.state.update_mission_status(
                    mission.id, MissionStatus.FAILED, f"Mission Failed: {len(failed_tasks)} tasks failed."
                )
            else:
                # انتهت كل المهام بنجاح!
                await self.state.update_mission_status(
                    mission.id, MissionStatus.SUCCESS, "Mission Accomplished successfully."
                )
                await self.state.log_event(mission.id, MissionEventType.MISSION_COMPLETED, {})
            return True

        # 2. تحديد المهام الجاهزة للتنفيذ (Topological Sort Logic)
        task_map = {t.task_key: t for t in tasks}
        ready_to_run = []

        for task in pending_tasks:
            dependencies = task.depends_on_json or []
            can_run = True
            for dep_key in dependencies:
                parent_task = task_map.get(dep_key)
                if not parent_task or parent_task.status != TaskStatus.SUCCESS:
                    can_run = False
                    break

            if can_run:
                ready_to_run.append(task)

        # 3. تشغيل المهام الجاهزة (Execution Batch)
        MAX_PARALLEL_EXECUTION = 5
        batch = ready_to_run[:MAX_PARALLEL_EXECUTION]

        if batch:
            logger.info(f"Overmind: Launching {len(batch)} tasks via SuperBrain.")
            coroutines = [self._execute_single_task(t) for t in batch]
            await asyncio.gather(*coroutines)

        return False

    async def _execute_single_task(self, task: Any) -> None:
        """
        تنفيذ مهمة واحدة وتحديث حالتها باستخدام الدماغ الخارق.
        """
        try:
            # تحديث الحالة إلى "جار التنفيذ"
            await self.state.mark_task_running(task.id)

            # استدعاء الدماغ الخارق للتنفيذ والتدقيق
            # We map the Task model to a dict-like structure if needed by the agent,
            # but our Operator supports the Task model.

            # Since Operator expects a task object with .tool_name etc, we pass 'task' directly.
            result = await self.brain.execute_task_with_oversight(task)

            # معالجة النتيجة
            if result["status"] == "success":
                await self.state.mark_task_complete(
                    task.id,
                    result_text=result.get("result_text", str(result)),
                    meta=result.get("meta", {})
                )
            else:
                error_msg = result.get("error", "Unknown Error")
                await self.state.mark_task_failed(task.id, error_msg)

        except Exception as e:
            logger.error(f"Task Execution Crashed: {e}")
            await self.state.mark_task_failed(task.id, f"Crash: {str(e)}")

    async def _handle_catastrophic_failure(self, mission_id: int, error: Exception) -> None:
        """
        معالجة الانهيارات الكلية للمهمة.
        """
        await self.state.update_mission_status(
            mission_id, MissionStatus.FAILED, f"System Crash: {error}"
        )
        await self.state.log_event(
            mission_id,
            MissionEventType.MISSION_FAILED,
            {"error": str(error), "reason": "catastrophic_crash"},
        )
