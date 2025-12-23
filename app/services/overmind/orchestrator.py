# app/services/overmind/orchestrator.py
# =================================================================================================
# OVERMIND ORCHESTRATOR – COGNITIVE CORE
# Version: 12.0.0-super-agent
# =================================================================================================

import asyncio
import logging

from app.models import Mission, MissionEventType, MissionStatus
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.state import MissionStateManager
from app.services.overmind.domain.cognitive import SuperBrain

logger = logging.getLogger(__name__)


class OvermindOrchestrator:
    """
    Overmind Orchestrator (The Cognitive Brain).

    This class serves as the central command center for the AI's autonomous operations.
    It manages the entire lifecycle of a "Mission" (a high-level user request) by coordinating
    between specialized sub-systems: Planning and Execution.

    Key Responsibilities (The Role):
    1.  **Mission Lifecycle Management**: Transitions missions through states (PENDING -> PLANNING -> PLANNED -> RUNNING -> SUCCESS/FAILED).
    2.  **Strategic Planning**: Selects and invokes the appropriate AI Planner to break down complex objectives into executable tasks.
    3.  **Execution Coordination**: Monitors the state of tasks, resolving dependencies (Topological Sort), and scheduling them for execution.
    4.  **Resilience**: Handles failures, ensuring the system can recover or gracefully terminate catastrophic errors.

    Why this class exists:
    To implement the "Plan-Execute" cognitive architecture, allowing the AI to solve complex,
    multi-step problems autonomously without constant human intervention.
    """

    def __init__(
        self,
        state_manager: MissionStateManager,
        executor: TaskExecutor,
        brain: SuperBrain | None = None,
    ):
        """
        Initialize the Orchestrator with its dependencies.

        Args:
            state_manager (MissionStateManager): Handles persistence.
            executor (TaskExecutor): The "Hands" of the system.
            brain (SuperBrain): The "Council of Wisdom" logic.
        """
        self.state = state_manager
        self.executor = executor
        self.brain = brain

    async def run_mission(self, mission_id: int):
        """
        Main entry point for the Async Mission Lifecycle.
        Now delegates cognitive load to the SuperBrain (Council of Wisdom).
        """
        try:
            mission = await self.state.get_mission(mission_id)
            if not mission:
                logger.error(f"Mission {mission_id} not found.")
                return

            if self.brain:
                # V12: Super Agent Path
                await self._run_super_agent_loop(mission)
            else:
                # Fallback to Legacy Loop (if brain not injected)
                logger.warning("SuperBrain not found, using legacy loop.")
                pass  # Or implement fallback

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

    async def _run_super_agent_loop(self, mission: Mission):
        """
        The new, streamlined, autonomous loop driven by the Council of Wisdom.
        """
        await self.state.update_mission_status(
            mission.id, MissionStatus.RUNNING, "Council of Wisdom Convening"
        )

        try:
            # The Brain handles the entire Plan -> Design -> Review -> Execute loop
            # This is 100% autonomous and self-correcting.
            if self.brain:
                result = await self.brain.process_mission(mission)

            await self.state.update_mission_status(
                mission.id, MissionStatus.SUCCESS, "Mission Accomplished by Super Agent"
            )
            await self.state.log_event(
                mission.id,
                MissionEventType.MISSION_COMPLETED,
                {"result": result}
            )

        except Exception as e:
            logger.error(f"SuperBrain failure: {e}")
            await self.state.update_mission_status(
                mission.id, MissionStatus.FAILED, f"Cognitive Error: {e}"
            )
