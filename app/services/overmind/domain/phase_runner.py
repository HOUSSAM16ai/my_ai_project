"""
Cognitive Phase Runner.
-----------------------
Encapsulates the execution logic for cognitive phases, handling logging,
session recording, and memory snapshots.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.protocols import AgentMemory
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.domain.council_session import CouncilSession
from app.services.overmind.domain.enums import CognitiveEvent, CognitivePhase
from app.services.overmind.domain.primitives import EventLogger

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CognitivePhaseRunner:
    """
    Executes cognitive phases with standardized logging, session recording, and memory capture.
    """

    def __init__(self, memory_agent: AgentMemory | None = None) -> None:
        self.memory_agent = memory_agent

    async def create_safe_logger(
        self, log_event: Callable[[str, dict[str, object]], Awaitable[None]] | None
    ) -> EventLogger:
        """
        Create a safe event logger function.
        """

        async def safe_log(evt_type: str, data: dict[str, object]) -> None:
            if log_event:
                await log_event(evt_type, data)

        return safe_log

    async def execute_agent_action(
        self,
        *,
        phase_name: str | CognitivePhase,
        agent_name: str,
        action: Callable[[], Awaitable[T]],
        timeout: float,
        log_func: EventLogger,
        session: CouncilSession | None,
        input_data: dict[str, object],
        collab_context: InMemoryCollaborationContext,
    ) -> T:
        """
        Execute an agent action within a phase, recording the session and capturing memory.
        """
        phase_label = str(phase_name)
        try:
            result = await self.execute_phase(
                phase_name=phase_name,
                agent_name=agent_name,
                action=action,
                timeout=timeout,
                log_func=log_func,
            )
            self.record_session_action(
                session=session,
                agent_name=agent_name,
                phase_label=phase_label,
                input_data=input_data,
                output_data=result,  # type: ignore
                success=True,
                error_message=None,
            )
            await self.capture_memory_snapshot(
                collab_context=collab_context,
                agent_name=agent_name,
                phase_label=phase_label,
                input_data=input_data,
                output_data=result,  # type: ignore
                error_message=None,
            )
            return result
        except Exception as exc:
            self.record_session_action(
                session=session,
                agent_name=agent_name,
                phase_label=phase_label,
                input_data=input_data,
                output_data={"error": str(exc)},
                success=False,
                error_message=str(exc),
            )
            await self.capture_memory_snapshot(
                collab_context=collab_context,
                agent_name=agent_name,
                phase_label=phase_label,
                input_data=input_data,
                output_data=None,
                error_message=str(exc),
            )
            raise

    async def execute_phase(
        self,
        *,
        phase_name: str | CognitivePhase,
        agent_name: str,
        action: Callable[[], Awaitable[T]],
        timeout: float,
        log_func: EventLogger,
    ) -> T:
        """
        Generic cognitive phase executor with timeout handling.
        """
        await log_func(CognitiveEvent.PHASE_START, {"phase": phase_name, "agent": agent_name})
        try:
            result = await asyncio.wait_for(action(), timeout=timeout)
            phase_str = self.phase_event_label(phase_name)
            await log_func(f"{phase_str}_completed", {"summary": "Phase completed successfully"})
            return result
        except TimeoutError:
            error_msg = f"{agent_name} timeout during {phase_name} (exceeded {timeout}s)"
            logger.error(error_msg)
            phase_str = self.phase_event_label(phase_name)
            await log_func(f"{phase_str}_timeout", {"error": error_msg})
            raise RuntimeError(error_msg) from None

    def record_session_action(
        self,
        *,
        session: CouncilSession | None,
        agent_name: str,
        phase_label: str,
        input_data: dict[str, object],
        output_data: dict[str, object] | None,
        success: bool,
        error_message: str | None,
    ) -> None:
        """
        Record action in the council session.
        """
        if not session:
            return
        session.record_action(
            agent_name=agent_name,
            action=phase_label,
            input_data=input_data,
            output_data=output_data or {},
            success=success,
            error_message=error_message,
        )

    async def capture_memory_snapshot(
        self,
        *,
        collab_context: InMemoryCollaborationContext,
        agent_name: str,
        phase_label: str,
        input_data: dict[str, object],
        output_data: dict[str, object] | None,
        error_message: str | None,
    ) -> None:
        """
        Capture a memory snapshot of the phase execution.
        """
        if not self.memory_agent:
            return
        payload, label_suffix = self.build_memory_payload(
            agent_name=agent_name,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
        )
        await self.memory_agent.capture_memory(
            collab_context,
            label=f"{phase_label}{label_suffix}",
            payload=payload,
        )

    @staticmethod
    def build_memory_payload(
        *,
        agent_name: str,
        input_data: dict[str, object],
        output_data: dict[str, object] | None,
        error_message: str | None,
    ) -> tuple[dict[str, object], str]:
        """
        Build the memory payload.
        """
        payload: dict[str, object] = {
            "agent": agent_name,
            "input": input_data,
        }
        label_suffix = ""
        if error_message:
            payload["error"] = error_message
            label_suffix = "_error"
        if output_data is not None:
            payload["output"] = output_data
        return payload, label_suffix

    @staticmethod
    def phase_event_label(phase_name: str | CognitivePhase) -> str:
        """
        Normalize phase name for event labeling.
        """
        return str(phase_name).lower()
