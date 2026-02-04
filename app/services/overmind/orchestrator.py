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
- Dependency Inversion: الاعتماد على البروتوكولات.
"""

import logging
from typing import TYPE_CHECKING

from app.core.domain.mission import Mission, MissionEventType, MissionStatus
from app.core.protocols import MissionStateManagerProtocol, TaskExecutorProtocol
from app.services.overmind.domain.enums import OvermindMessage

if TYPE_CHECKING:
    from app.services.overmind.domain.cognitive import SuperBrain

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
        *,
        state_manager: MissionStateManagerProtocol,
        executor: TaskExecutorProtocol,
        brain: "SuperBrain",
    ) -> None:
        """
        تهيئة المنسق مع التبعيات اللازمة.

        Args:
            state_manager (MissionStateManagerProtocol): مدير حالة المهمة.
            executor (TaskExecutorProtocol): الذراع التنفيذي.
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
            mission.id, MissionStatus.RUNNING, OvermindMessage.CONVENING_COUNCIL
        )

        async def _log_bridge(evt_type: str, payload: dict[str, object]) -> None:
            """
            جسر (Bridge) للربط بين أحداث العقل ومدير الحالة.
            """
            await self.state.log_event(
                mission.id,
                MissionEventType.STATUS_CHANGE,
                {"brain_event": evt_type, "data": payload},
            )

        try:
            # تفويض كامل للعقل (Abstraction Barrier)
            result = await self.brain.process_mission(mission, log_event=_log_bridge)

            # Extract summary for Admin Dashboard visibility
            summary = self._extract_summary(result)

            await self.state.complete_mission(
                mission.id, result_summary=summary, result_json=result
            )

        except Exception as e:
            logger.exception(f"SuperBrain failure in mission {mission.id}: {e}")
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"Cognitive Error: {e}"
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.MISSION_FAILED,
                {"error": str(e), "error_type": type(e).__name__},
            )

    def _extract_summary(self, result: dict[str, object]) -> str:
        """
        استخراج ملخص نصي للنتيجة لعرضه في لوحة الإدارة.
        Extracts a text summary for the Admin Dashboard.
        """
        if not result:
            return "تمت المهمة بنجاح."

        # 1. Try explicit summary/output fields
        if result.get("summary"):
            return str(result["summary"])
        if result.get("output"):
            return str(result["output"])
        if result.get("answer"):
            return str(result["answer"])

        # 2. Handle OperatorAgent results list
        if "results" in result and isinstance(result["results"], list):
            tasks = result["results"]
            lines = [f"✅ Executed {len(tasks)} tasks:"]
            for t in tasks:
                if isinstance(t, dict):
                    name = t.get("name", "Task")
                    res = t.get("result", {})
                    # If result is a dict with result_text (Executor format)
                    val = res.get("result_text") if isinstance(res, dict) else str(res)
                    # Truncate if too long
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    lines.append(f"- {name}: {val_str}")
            return "\n".join(lines)

        # 3. Fallback to string representation
        return str(result)[:500]
