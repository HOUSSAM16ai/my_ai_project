# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE
# Version: 12.1.0-super-agent (Refactored)
# =================================================================================================

"""
منسق العقل المدبر (Overmind Orchestrator).

هذه الفئة تمثل مركز القيادة والسيطرة للوكلاء المستقلين.
تقوم بإدارة دورة حياة "المهمة" (Mission) بالكامل من خلال تنسيق العمل بين الأنظمة الفرعية:
التخطيط (Planning) والتنفيذ (Execution).

المعايير الرئيسية:
- Abstraction: تفويض كامل للمنطق المعرفي إلى `SuperBrain`.
- Strictness: عدم وجود منطق "Legacy" أو مسارات بديلة.
- Resilience: معالجة شاملة للأخطاء على المستوى الأعلى.
"""

import logging
from typing import Any

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
        brain: SuperBrain,
    ) -> None:
        """
        تهيئة المنسق مع التبعيات اللازمة.

        Args:
            state_manager (MissionStateManager): مدير حالة المهمة.
            executor (TaskExecutor): الذراع التنفيذي.
            brain (SuperBrain): العقل المفكر (Council of Wisdom).
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

            await self._run_super_agent_loop(mission)

        except Exception as e:
            # Catch-all for catastrophic failures preventing the loop from starting
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
        الحلقة الذاتية المدفوعة بمجلس الحكمة (Council of Wisdom).

        Args:
            mission (Mission): كائن المهمة.
        """
        await self.state.update_mission_status(
            mission.id, MissionStatus.RUNNING, "Council of Wisdom Convening"
        )

        async def _log_bridge(evt_type: str, payload: dict[str, Any]) -> None:
            """
            جسر (Bridge) للربط بين أحداث العقل ومدير الحالة.
            """
            await self.state.log_event(
                mission.id,
                MissionEventType.STATUS_CHANGE,
                {"brain_event": evt_type, "data": payload}
            )

        try:
            # تفويض كامل للعقل (Abstraction Barrier)
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
