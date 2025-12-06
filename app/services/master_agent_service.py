# app/services/master_agent_service.py
# =================================================================================================
# OVERMIND MASTER ORCHESTRATOR – LEGACY FACADE (Hyper-Bridge Adapter)
# Version: 11.0.0-hyper-async-adapter
# =================================================================================================
# EN OVERVIEW
#   This module acts as a Facade Pattern adapter, bridging legacy synchronous calls
#   to the new asynchronous "Overmind V11" Neural Architecture.
#   It ensures backward compatibility while the core engine runs on modern Async I/O.
# =================================================================================================

import asyncio
import logging
import threading
from typing import Any

from app.core.database import async_session_factory
from app.models import Mission, User
from app.services.overmind.core import OvermindOrchestrator
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.state import MissionStateManager

logger = logging.getLogger(__name__)


# =================================================================================================
# COMPATIBILITY WRAPPERS
# =================================================================================================

class OvermindService:
    """
    Legacy Service Wrapper.
    Translates synchronous method calls into asynchronous engine operations.
    """

    def start_new_mission(self, objective: str, initiator: User) -> Mission:
        """
        Starts a new mission.
        Returns the Mission object immediately (Synchronously),
        then launches the Async Orchestrator in a background thread/loop.
        """
        # 1. We need to create the mission synchronously to return it immediately
        #    However, our new logic is Async.
        #    We will use a temporary specialized run for creation.

        try:
            mission = self._run_sync(self._create_mission_async(objective, initiator.id))

            # 2. Launch the Orchestrator Background Process
            #    Fire and forget.
            threading.Thread(
                target=self._launch_orchestrator_thread,
                args=(mission.id,),
                daemon=True
            ).start()

            return mission
        except Exception as e:
            logger.error(f"Failed to start mission via Facade: {e}")
            raise

    def run_mission_lifecycle(self, mission_id: int):
        """
        Legacy entry point for the lifecycle thread.
        Now just delegates to the Async Orchestrator.
        """
        self._launch_orchestrator_thread(mission_id)

    # --- Internal Helpers ---

    def _run_sync(self, coroutine):
        """
        Helper to run an async coroutine synchronously.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
             # If we are already in a loop (e.g. FastAPI), we shouldn't be calling this
             # blocking method ideally, but for the Facade return value we might have to.
             # However, start_new_mission is usually called from an endpoint.
             # If we block the event loop, we hurt performance.
             # Ideally, we should change the controller to be async.
             # But strictly adhering to the legacy interface:
             import concurrent.futures
             with concurrent.futures.ThreadPoolExecutor() as pool:
                 future = pool.submit(asyncio.run, coroutine)
                 return future.result()
        else:
            return loop.run_until_complete(coroutine)

    async def _create_mission_async(self, objective: str, user_id: int) -> Mission:
        async with async_session_factory() as session:
            state = MissionStateManager(session)
            return await state.create_mission(objective, user_id)

    def _launch_orchestrator_thread(self, mission_id: int):
        """
        Runs the async orchestrator in a new event loop on this thread.
        """
        asyncio.run(self._run_orchestrator_async(mission_id))

    async def _run_orchestrator_async(self, mission_id: int):
        async with async_session_factory() as session:
            state = MissionStateManager(session)
            executor = TaskExecutor()
            orchestrator = OvermindOrchestrator(state, executor)
            await orchestrator.run_mission(mission_id)


# Singleton Instance
_overmind_service_singleton = OvermindService()


# =================================================================================================
# PUBLIC API EXPORTS (Legacy Interface)
# =================================================================================================

def start_mission(objective: str, initiator: User) -> Mission:
    return _overmind_service_singleton.start_new_mission(objective, initiator)

def run_mission_lifecycle(mission_id: int):
    return _overmind_service_singleton.run_mission_lifecycle(mission_id)
