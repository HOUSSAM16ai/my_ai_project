# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE (العقل المدبر)
# Version: 12.0.0-super-intelligence
# =================================================================================================

import asyncio
import logging
from typing import Any

from app.models import Mission, MissionEventType, MissionStatus, TaskStatus
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.planning.factory import get_all_planners
from app.services.overmind.state import MissionStateManager

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

    Why this class is simple yet powerful:
    It uses a robust State Machine loop (`_run_lifecycle_loop`) to decouple "Thinking" from "Acting",
    allowing the agent to pause, reflect, and resume at any time.
    """

    def __init__(self, state_manager: MissionStateManager, executor: TaskExecutor):
        """
        تهيئة العقل المدبر.

        Args:
            state_manager: مدير الذاكرة (يحفظ حالة المهمة والخطوات).
            executor: الذراع المنفذة (تقوم بتنفيذ الأوامر فعلياً).
        """
        self.state = state_manager
        self.executor = executor

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
        مرحلة التخطيط: تحويل الهدف إلى خطة عمل.
        """
        logger.info(f"Overmind: Planning for Mission {mission.id}...")
        await self.state.update_mission_status(
            mission.id, MissionStatus.PLANNING, "Thinking... (Generating Plan)"
        )

        # البحث عن مخططين أذكياء
        planners = get_all_planners()
        if not planners:
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, "Error: No brain (planner) found!"
            )
            return

        # اختيار المخطط الأول (يمكن تطويره ليختار الأذكى بناءً على نوع المهمة)
        planner = planners[0]

        try:
            # تنفيذ التخطيط (قد يستغرق وقتاً)
            # ندعم التخطيط المتزامن وغير المتزامن بمرونة فائقة
            if hasattr(planner, "a_instrumented_generate"):
                result = await planner.a_instrumented_generate(mission.objective)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, planner.instrumented_generate, mission.objective
                )

            plan_schema = result["plan"]
            meta = result["meta"]

            # حفظ الخطة في الذاكرة
            await self.state.persist_plan(
                mission.id,
                planner_name=getattr(planner, "name", "Unknown Planner"),
                plan_schema=plan_schema,
                score=meta.get("selection_score", 1.0),
                rationale="Selected by Overmind Intelligence",
            )

            # الانتقال للمرحلة التالية
            await self.state.update_mission_status(
                mission.id, MissionStatus.PLANNED, "Plan Ready. Engaging engines."
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.PLAN_SELECTED,
                {"planner": getattr(planner, "name", "unknown")},
            )

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"Planning Brain Failure: {e}"
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
        # المهمة جاهزة فقط إذا انتهت كل المهام التي تعتمد عليها بنجاح
        task_map = {t.task_key: t for t in tasks}
        ready_to_run = []

        for task in pending_tasks:
            dependencies = task.depends_on_json or []
            can_run = True
            for dep_key in dependencies:
                parent_task = task_map.get(dep_key)
                # إذا لم نجد المهمة الأب أو لم تنته بنجاح، لا يمكننا البدء
                if not parent_task or parent_task.status != TaskStatus.SUCCESS:
                    can_run = False
                    break

            if can_run:
                ready_to_run.append(task)

        # 3. تشغيل المهام الجاهزة (Execution Batch)
        # نحدد حداً أقصى للتوازي لتجنب استهلاك كل الموارد
        MAX_PARALLEL_EXECUTION = 5
        batch = ready_to_run[:MAX_PARALLEL_EXECUTION]

        if batch:
            logger.info(f"Overmind: Launching {len(batch)} tasks in parallel.")
            # إطلاق المهام بشكل متزامن (Asynchronous Fire-and-Forget / Gather)
            coroutines = [self._execute_single_task(t) for t in batch]
            # نستخدم gather لانتظار هذه الدفعة (أو يمكن إطلاقها في الخلفية في أنظمة أعقد)
            # هنا ننتظرها لتبسيط المنطق في هذه النسخة
            await asyncio.gather(*coroutines)

        return False

    async def _execute_single_task(self, task: Any) -> None:
        """
        تنفيذ مهمة واحدة وتحديث حالتها.
        """
        try:
            # تحديث الحالة إلى "جار التنفيذ"
            await self.state.mark_task_running(task.id)

            # استدعاء المنفذ (Executor)
            result = await self.executor.execute_task(task)

            # معالجة النتيجة
            if result["status"] == "success":
                await self.state.mark_task_complete(
                    task.id,
                    result_text=result["result_text"],
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
