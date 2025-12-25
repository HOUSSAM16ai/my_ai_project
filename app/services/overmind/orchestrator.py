# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE
# Version: 12.0.0-super-agent
# =================================================================================================

"""
منسق العقل المدبر (Overmind Orchestrator).

هذه الفئة تمثل مركز القيادة والسيطرة للوكلاء المستقلين.
تقوم بإدارة دورة حياة "المهمة" (Mission) بالكامل من خلال تنسيق العمل بين الأنظمة الفرعية:
التخطيط (Planning) والتنفيذ (Execution).

المسؤوليات الرئيسية:
1. إدارة دورة حياة المهمة: تحويل المهمة عبر الحالات (PENDING -> RUNNING -> SUCCESS).
2. التخطيط الاستراتيجي: استدعاء العقل الخارق (SuperBrain) لتحليل الأهداف المعقدة.
3. تنسيق التنفيذ: مراقبة حالة المهام وجدولتها للتنفيذ.
4. الصمود (Resilience): معالجة الأخطاء وضمان استعادة النظام عافيته.

المعايير (Standards):
- SICP: فصل المنطق (Brain) عن الحالة (State).
- CS50 2025: صرامة النوع (Type Strictness) والتوثيق العربي.
"""

import logging
from collections.abc import Callable

from app.models import Mission, MissionEventType, MissionStatus
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.state import MissionStateManager

logger = logging.getLogger(__name__)

__all__ = ["OvermindOrchestrator"]


class OvermindOrchestrator:
    """
    منسق العقل المدبر (The Cognitive Brain).

    يعمل هذا الصف كجسر بين "الرغبة" (User Intent) و "الواقع" (System Actions).
    لا يحتوي على منطق معقد بحد ذاته، بل يقوم بتفويض المهام لمكونات متخصصة (Brain, Executor, State).
    """

    def __init__(
        self,
        state_manager: MissionStateManager,
        executor: TaskExecutor,
        brain: SuperBrain | None = None,
    ) -> None:
        """
        تهيئة المنسق مع التبعيات اللازمة.

        Args:
            state_manager (MissionStateManager): مدير حالة المهمة (Persistence).
            executor (TaskExecutor): الذراع التنفيذي للنظام (The Hands).
            brain (SuperBrain | None): العقل المفكر (Council of Wisdom).
        """
        self.state = state_manager
        self.executor = executor
        self.brain = brain

    async def run_mission(self, mission_id: int) -> None:
        """
        نقطة الدخول الرئيسية لدورة حياة المهمة غير المتزامنة.
        تقوم بتفويض الحمل المعرفي للعقل الخارق (SuperBrain).

        Args:
            mission_id (int): معرف المهمة في قاعدة البيانات.
        """
        try:
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.error(f"Mission {mission_id} not found.")
                return

            if self.brain:
                # المسار الجديد: الوكيل الخارق
                await self._run_super_agent_loop(mission)
            else:
                # المسار القديم: في حال عدم وجود العقل (للتوافق)
                logger.warning("SuperBrain not found, using legacy loop.")
                await self.state.log_event(
                    mission_id,
                    MissionEventType.STATUS_CHANGE,
                    {"warning": "SuperBrain not injected"}
                )

        except Exception as e:
            logger.exception(f"Catastrophic failure in Mission {mission_id}")
            await self.state.update_mission_status(
                mission_id, MissionStatus.FAILED, note=f"Fatal Error: {e}"
            )
            await self.state.log_event(
                mission_id,
                MissionEventType.MISSION_FAILED,
                {"error": str(e), "reason": "catastrophic_crash"},
            )

    async def _run_super_agent_loop(self, mission: Mission) -> None:
        """
        الحلقة الذاتية المبسطة المدفوعة بمجلس الحكمة (Council of Wisdom).

        Args:
            mission (Mission): كائن المهمة.
        """
        await self.state.update_mission_status(
            mission.id, MissionStatus.RUNNING, "Council of Wisdom Convening"
        )

        async def _log_bridge(evt_type: str, payload: dict) -> None:
            """
            جسر للربط بين أحداث العقل ومدير الحالة.
            """
            # يمكن تخصيص نوع الحدث هنا بناءً على مخرجات العقل
            await self.state.log_event(
                mission.id,
                MissionEventType.STATUS_CHANGE,
                {"brain_event": evt_type, "data": payload}
            )

        try:
            # العقل يتولى مسؤولية حلقة: خطط -> صمم -> راجع -> نفذ
            # This is 100% autonomous and self-correcting.
            result = {}
            if self.brain:
                await self.state.log_event(
                    mission.id,
                    MissionEventType.STATUS_CHANGE,
                    {"phase": "brain_processing_started"}
                )
                result = await self.brain.process_mission(
                    mission,
                    log_event=_log_bridge
                )

            await self.state.update_mission_status(
                mission.id, MissionStatus.SUCCESS, "Mission Accomplished by Super Agent"
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.MISSION_COMPLETED,
                {"result": result}
            )

        except Exception as e:
            logger.exception(f"SuperBrain failure in mission {mission.id}: {e}")
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"Cognitive Error: {e}"
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.MISSION_FAILED,
                {"error": str(e), "error_type": type(e).__name__}
            )
