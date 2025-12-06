# app/services/overmind/core.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE
# Version: 11.0.0-hyper-async
# =================================================================================================

import asyncio
import logging
import time
from datetime import UTC, datetime

from app.models import Mission, MissionEventType, MissionStatus, TaskStatus
from app.overmind.planning.factory import get_all_planners
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.state import MissionStateManager

logger = logging.getLogger(__name__)


class OvermindOrchestrator:
    """
    The Brain. Coordinates the Planning-Execution loop asynchronously.
    """

    def __init__(self, state_manager: MissionStateManager, executor: TaskExecutor):
        self.state = state_manager
        self.executor = executor

    async def run_mission(self, mission_id: int):
        """
        Main entry point for the Async Mission Lifecycle.
        """
        mission = await self.state.get_mission(mission_id)
        if not mission:
            logger.error(f"Mission {mission_id} not found.")
            return

        try:
            await self._run_lifecycle_loop(mission_id)
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

    async def _run_lifecycle_loop(self, mission_id: int):
        # Configuration
        MAX_TICKS = 1500
        POLL_INTERVAL = 0.5

        for _ in range(MAX_TICKS):
            # 1. Refresh State
            mission = await self.state.get_mission(mission_id)
            if not mission:
                break

            status = mission.status

            # 2. State Machine
            if status == MissionStatus.PENDING:
                await self._phase_planning(mission)

            elif status == MissionStatus.PLANNING:
                # Wait for planning (if we offload it, but here we do it inline usually)
                await asyncio.sleep(POLL_INTERVAL)

            elif status == MissionStatus.PLANNED:
                await self._phase_prepare_execution(mission)

            elif status == MissionStatus.RUNNING:
                all_done = await self._phase_execution_step(mission)
                if all_done:
                    break
                await asyncio.sleep(POLL_INTERVAL)

            elif status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                logger.info(f"Mission {mission_id} reached terminal state: {status}")
                break

            else:
                await asyncio.sleep(POLL_INTERVAL)

    async def _phase_planning(self, mission: Mission):
        await self.state.update_mission_status(mission.id, MissionStatus.PLANNING, "Starting Planning Phase")

        # Select Planner
        planners = get_all_planners()
        if not planners:
            await self.state.update_mission_status(mission.id, MissionStatus.FAILED, "No planners available")
            return

        # Simple logic: Pick the first available one or highest score (Mock logic for now)
        # In a real Hyper-Advanced system, we'd run them in parallel.
        planner = planners[0]

        try:
            # Use Async generation if available
            if hasattr(planner, 'a_instrumented_generate'):
                result = await planner.a_instrumented_generate(mission.objective)
            else:
                # Fallback to sync in thread
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, planner.instrumented_generate, mission.objective)

            plan_schema = result["plan"]
            meta = result["meta"]

            # Persist
            await self.state.persist_plan(
                mission.id,
                planner_name=getattr(planner, "name", "unknown"),
                plan_schema=plan_schema,
                score=meta.get("selection_score", 1.0),
                rationale="Selected via Orchestrator V2"
            )

            await self.state.update_mission_status(mission.id, MissionStatus.PLANNED, "Plan generated successfully")

            await self.state.log_event(
                mission.id,
                MissionEventType.PLAN_SELECTED,
                {"planner": getattr(planner, "name", "unknown")}
            )

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            await self.state.update_mission_status(mission.id, MissionStatus.FAILED, f"Planning Exception: {e}")

    async def _phase_prepare_execution(self, mission: Mission):
        await self.state.update_mission_status(mission.id, MissionStatus.RUNNING, "Execution Started")
        await self.state.log_event(mission.id, MissionEventType.EXECUTION_STARTED, {})

    async def _phase_execution_step(self, mission: Mission) -> bool:
        """
        Executes ready tasks. Returns True if mission is finished.
        """
        tasks = await self.state.get_tasks(mission.id)

        # Check Terminal Conditions
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]
        running = [t for t in tasks if t.status == TaskStatus.RUNNING]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]

        if not pending and not running:
            if failed:
                await self.state.update_mission_status(mission.id, MissionStatus.FAILED, f"{len(failed)} tasks failed.")
                await self.state.log_event(mission.id, MissionEventType.MISSION_FAILED, {"failed_count": len(failed)})
            else:
                await self.state.update_mission_status(mission.id, MissionStatus.SUCCESS, "All tasks completed.")
                await self.state.log_event(mission.id, MissionEventType.MISSION_COMPLETED, {})
            return True

        # Identify Ready Tasks (Topological)
        # A task is ready if PENDING and all deps are SUCCESS
        task_map = {t.task_key: t for t in tasks}

        ready_tasks = []
        for t in pending:
            deps = t.depends_on_json or []
            deps_met = True
            for d in deps:
                parent = task_map.get(d)
                if not parent or parent.status != TaskStatus.SUCCESS:
                    deps_met = False
                    break

            if deps_met:
                ready_tasks.append(t)

        # Execute Batch (Async Parallel)
        MAX_PARALLEL = 5
        batch = ready_tasks[:MAX_PARALLEL]

        if not batch and not running:
             # Stall detection?
             pass

        tasks_coroutines = []
        for t in batch:
            tasks_coroutines.append(self._execute_single_task(t))

        if tasks_coroutines:
            await asyncio.gather(*tasks_coroutines)

        return False

    async def _execute_single_task(self, task):
        await self.state.mark_task_running(task.id)

        res = await self.executor.execute_task(task)

        if res["status"] == "success":
            await self.state.mark_task_complete(task.id, res["result_text"], res.get("meta", {}))
        else:
            await self.state.mark_task_failed(task.id, res.get("error", "Unknown error"))
