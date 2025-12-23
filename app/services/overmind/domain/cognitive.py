# app/services/overmind/domain/cognitive.py
# =================================================================================================
# SUPER BRAIN – COGNITIVE DOMAIN (الدماغ الخارق)
# =================================================================================================

import logging
from typing import Any

from app.core.protocols import AgentPlanner, AgentExecutor, AgentReflector
from app.models import Mission

logger = logging.getLogger(__name__)

class SuperBrain:
    """
    الدماغ الخارق (SuperBrain).

    هذا الكلاس يمثل "الغرفة المركزية" التي يجتمع فيها الوكلاء المتخصصون لاتخاذ القرارات.
    إنه يفصل منطق "التفكير" (Thinking) عن منطق "إدارة الحالة" (State Management) الموجود في Orchestrator.

    The Council:
    - The Strategist (Planner): يضع الخطط.
    - The Operator (Executor): ينفذ المهام.
    - The Auditor (Reflector): يراجع ويصحح.
    """

    def __init__(
        self,
        planner: AgentPlanner,
        executor: AgentExecutor,
        reflector: AgentReflector
    ):
        self.planner = planner
        self.executor = executor
        self.reflector = reflector

    async def think_and_plan(self, objective: str) -> dict[str, Any]:
        """
        دورة التفكير والتخطيط مع النقد الذاتي.
        Generates a plan, critiques it, and refines it.
        """
        logger.info(f"SuperBrain: Convening the council for objective: {objective[:30]}...")

        # 1. التخطيط الأولي (Initial Planning)
        plan = await self.planner.create_plan(objective)

        # 2. النقد والمراجعة (Critique & Reflection)
        critique = await self.reflector.critique_plan(plan, objective)

        if not critique["valid"]:
            logger.warning(f"SuperBrain: Plan rejected by Auditor. Feedback: {critique['feedback']}")
            # هنا يمكننا طلب إعادة التخطيط بناءً على الملاحظات (Loop)
            # For this version, we append the feedback to the plan for context
            plan["warnings"] = critique["feedback"]
        else:
            logger.info("SuperBrain: Plan ratified by the Council.")

        return plan

    async def execute_task_with_oversight(self, task: Any) -> dict[str, Any]:
        """
        تنفيذ مهمة تحت رقابة المدقق.
        Executes a task and verifies the result immediately.
        """
        logger.info(f"SuperBrain: Authorizing execution of Task {getattr(task, 'id', 'Unknown')}")

        # 1. التنفيذ (Execution)
        result = await self.executor.execute_task(task)

        # 2. التحقق (Verification)
        verification = await self.reflector.verify_execution(task, result)

        if not verification["verified"]:
            logger.error(f"SuperBrain: Task verification failed! {verification['reason']}")
            result["status"] = "failed"
            result["error"] = f"Verification Failed: {verification['reason']}"

        return result
