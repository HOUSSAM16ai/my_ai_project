"""
عقدة المشرف الذكي (Smart Supervisor Node) - MAF-1.0 Kernel Edition.
-------------------------------------------------------------------
يعمل هذا المشرف كـ "نواة النسيج" (Fabric Kernel)، ويطبق بروتوكول MAF-1.0 بصرامة.
يحل محل التوجيه القائم على LLM بآلة حالة حتمية (Deterministic State Machine) لضمان الموثوقية.
"""

import logging

from app.core.ai_gateway import AIClient
from app.core.maf.kernel import MAFKernel
from app.services.chat.graph.state import AgentState

logger = logging.getLogger(__name__)


class SupervisorNode:
    """
    المشرف المتوافق مع MAF (The MAF-Compliant Supervisor).
    ينفذ دورة: Generate -> Attack -> Verify -> Seal.
    """

    @staticmethod
    async def decide_next_step(state: AgentState, _ai_client: AIClient) -> dict:
        """
        يقرر الخطوة التالية بناءً على بروتوكول MAF.
        """
        state.get("messages", [])

        # Memory Recall (Context Loading)
        # Even with deterministic routing, we might want to load memory to pass to workers?
        # Ideally, workers recall their own memory, or Supervisor injects it.
        # We will keep the recall logic but just log it or pass it if needed.
        # For now, we trust the workers to do their job or the Kernel instruction to be sufficient.

        try:
            # Execute MAF Kernel Logic
            decision = MAFKernel.decide_next_node(state)

            next_node = decision["next"]
            instruction = decision["instruction"]
            increment_iteration = decision.get("increment_iteration", False)

            logger.info(f"MAF Kernel Decision: {next_node} | Instruction: {instruction[:50]}...")

            updates = {
                "next": next_node,
                "supervisor_instruction": instruction,
                "routing_trace": [{"node": next_node, "reason": "MAF Protocol Enforcement"}],
            }

            if increment_iteration:
                updates["iteration_count"] = state.get("iteration_count", 0) + 1

            return updates

        except Exception as e:
            logger.error(f"Supervisor (MAF Kernel) failed: {e}", exc_info=True)
            # Fail-safe Fallback
            return {
                "next": "writer",
                "supervisor_instruction": "CRITICAL KERNEL FAILURE. Synthesize immediate response apologizing for the error.",
            }


async def supervisor_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    غلاف (Wrapper) لعقدة المشرف ليتم استدعاؤها داخل LangGraph.
    """
    return await SupervisorNode.decide_next_step(state, ai_client)
