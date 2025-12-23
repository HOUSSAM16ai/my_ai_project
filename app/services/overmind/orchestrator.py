# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE (العقل المدبر)
# Version: 15.0.0-council-of-wisdom
# =================================================================================================

import asyncio
import logging
from typing import Any

from app.models import Mission, MissionEventType, MissionStatus, TaskStatus
from app.services.overmind.state import MissionStateManager
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.agents import (
    StrategistAgent,
    OperatorAgent,
    AuditorAgent,
    ArchitectAgent
)
from app.core.ai_gateway import AIClient
from app.services.agent_tools.infrastructure.registry import get_registry

logger = logging.getLogger(__name__)


class OvermindOrchestrator:
    """
    العقل المدبر (Overmind Orchestrator).

    يقوم بتنسيق "مجلس الحكماء" (Council of Wisdom) لتنفيذ المهام المعقدة.
    يعتمد على SuperBrain للفصل بين المنطق الإدراكي (Thinking) والمنطق التشغيلي (State).

    Architectural Pattern:
    Orchestrator (State/Lifecycle) -> SuperBrain (Cognition) -> Agents (Capabilities)
    """

    def __init__(self, state_manager: MissionStateManager, ai_client: AIClient | None = None):
        """
        تهيئة العقل المدبر.
        """
        self.state = state_manager

        # 1. AI Gateway & Tools
        self._ai = ai_client
        self._registry = get_registry()

        # 2. The Council of Agents (مجلس الحكماء)
        self.strategist = StrategistAgent(self._ai)
        self.architect = ArchitectAgent(self._ai)
        self.operator = OperatorAgent(self._registry)
        self.auditor = AuditorAgent(self._ai)

        # 3. The SuperBrain (The Coordinator)
        self.brain = SuperBrain(
            planner=self.strategist,
            architect=self.architect,
            executor=self.operator,
            reflector=self.auditor
        )

    async def run_mission(self, mission_id: int) -> None:
        """
        نقطة الانطلاق الرئيسية للمهمة.
        """
        try:
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.error(f"Mission {mission_id} not found in memory.")
                return

            await self._run_lifecycle_loop(mission_id)

        except Exception as e:
            logger.exception(f"Fatal error in Mission {mission_id}")
            await self._handle_catastrophic_failure(mission_id, e)

    async def _run_lifecycle_loop(self, mission_id: int) -> None:
        """
        حلقة الذكاء والتنفيذ.
        """
        MAX_CYCLES = 2000
        CYCLE_DELAY = 0.5

        logger.info(f"Overmind: Starting cognitive loop for Mission {mission_id}")

        for cycle in range(MAX_CYCLES):
            mission = await self.state.get_mission(mission_id)
            if not mission:
                break

            status = mission.status
            logger.debug(f"Cycle {cycle}: Mission Status = {status}")

            if status == MissionStatus.PENDING:
                await self._phase_planning(mission)

            elif status == MissionStatus.PLANNING:
                await asyncio.sleep(CYCLE_DELAY)

            elif status == MissionStatus.PLANNED:
                await self._phase_prepare_execution(mission)

            elif status == MissionStatus.RUNNING:
                is_finished = await self._phase_execution_monitor(mission)
                if is_finished:
                    break
                await asyncio.sleep(CYCLE_DELAY)

            elif status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                logger.info(f"Mission {mission_id} finished with state: {status}")
                break

            else:
                await asyncio.sleep(CYCLE_DELAY)

    async def _phase_planning(self, mission: Mission) -> None:
        """
        مرحلة التخطيط والتصميم.
        """
        logger.info(f"Overmind: Engaging SuperBrain for Mission {mission.id}...")
        await self.state.update_mission_status(
            mission.id, MissionStatus.PLANNING, "Council is convening..."
        )

        try:
            # استخدام الدماغ الخارق للتخطيط والتصميم
            plan_result = await self.brain.think_and_plan(mission.objective, mission.id)

            # التحقق من موافقة المجلس
            if not plan_result.get("approved", True):
                # إذا رفض المجلس الخطة، نفشل المهمة (لأننا لم نطبق حلقة التصحيح الذاتي الكاملة بعد)
                warnings = plan_result.get("warnings", "Unknown Objection")
                await self.state.update_mission_status(
                    mission.id, MissionStatus.FAILED, f"Plan Rejected by Council: {warnings}"
                )
                return

            # حفظ الخطة في الذاكرة
            await self.state.persist_plan(
                mission.id,
                planner_name=self.strategist.name,
                plan_schema=plan_result,
                score=1.0,
                rationale="Ratified by Council of Agents",
            )

            await self.state.update_mission_status(
                mission.id, MissionStatus.PLANNED, "Plan & Design Ready."
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.PLAN_SELECTED,
                {"planner": self.strategist.name, "architect": self.architect.name},
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
        مراقب التنفيذ.
        """
        tasks = await self.state.get_tasks(mission.id)

        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        running_tasks = [t for t in tasks if t.status == TaskStatus.RUNNING]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]

        if not pending_tasks and not running_tasks:
            if failed_tasks:
                await self.state.update_mission_status(
                    mission.id, MissionStatus.FAILED, f"Mission Failed: {len(failed_tasks)} tasks failed."
                )
            else:
                await self.state.update_mission_status(
                    mission.id, MissionStatus.SUCCESS, "Mission Accomplished successfully."
                )
                await self.state.log_event(mission.id, MissionEventType.MISSION_COMPLETED, {})
            return True

        # Topological Sort & Dependency Check
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

        # Batch Execution
        MAX_PARALLEL_EXECUTION = 5
        batch = ready_to_run[:MAX_PARALLEL_EXECUTION]

        if batch:
            logger.info(f"Overmind: Launching {len(batch)} tasks via SuperBrain.")
            coroutines = [self._execute_single_task(t, mission.id) for t in batch]
            await asyncio.gather(*coroutines)

        return False

    async def _execute_single_task(self, task: Any, mission_id: int) -> None:
        """
        تنفيذ مهمة واحدة وتحديث حالتها باستخدام الدماغ الخارق.
        """
        try:
            await self.state.mark_task_running(task.id)

            # Pass mission_id to give context to the agents
            result = await self.brain.execute_task_with_oversight(task, mission_id=mission_id)

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
        await self.state.update_mission_status(
            mission_id, MissionStatus.FAILED, f"System Crash: {error}"
        )
