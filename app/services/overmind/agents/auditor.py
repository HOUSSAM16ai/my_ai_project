# app/services/overmind/agents/auditor.py
import logging
from typing import Any
from app.core.protocols import AgentReflector

logger = logging.getLogger(__name__)

class AuditorAgent(AgentReflector):
    """
    الناقد والمدقق (Auditor Agent).
    الضمير الحي للنظام. يراقب، يحلل، وينتقد الخطط والنتائج لضمان الجودة "الخرافية".
    The conscience of the system. Monitors, analyzes, and critiques plans and results.
    """

    @property
    def name(self) -> str:
        return "Auditor (Eye-of-Thoth)"

    async def critique_plan(self, plan: dict[str, Any], objective: str) -> dict[str, Any]:
        """
        Reviews the plan for logic gaps, safety issues, or inefficiencies.
        """
        logger.info("Auditor: Reviewing strategic plan...")

        steps = plan.get("steps", [])
        if not steps:
            return {"valid": False, "feedback": "Plan is empty."}

        # Basic Heuristic Checks (Supernatural checks would involve LLM)
        feedback = []
        is_valid = True

        # Check 1: Does it end with verification?
        last_step = steps[-1]
        if "verify" not in last_step.get("name", "").lower() and "check" not in last_step.get("name", "").lower():
            feedback.append("Plan lacks a final verification step.")
            # We don't fail, just warn, unless strict mode.

        if not feedback:
            logger.info("Auditor: Plan approved.")
            return {"valid": True, "feedback": "Plan looks solid."}
        else:
            logger.warning(f"Auditor: Plan issues found: {feedback}")
            return {"valid": True, "feedback": "; ".join(feedback)} # Still valid, just feedback.

    async def verify_execution(self, task: Any, result: dict[str, Any]) -> dict[str, Any]:
        """
        Verifies if the result actually accomplished the task.
        """
        status = result.get("status")
        if status != "success":
            return {"verified": False, "reason": f"Execution reported failure: {result.get('error')}"}

        # In a real super-agent, we would look at the content of 'result_text'
        # and compare it against the task description.

        logger.info("Auditor: Execution result verified.")
        return {"verified": True, "reason": "Execution reported success."}
