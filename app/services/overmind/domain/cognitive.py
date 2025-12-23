# app/services/overmind/domain/cognitive.py
# =================================================================================================
# SUPER BRAIN – COGNITIVE DOMAIN (الدماغ الخارق)
# =================================================================================================

import logging
from typing import Any

from app.core.protocols import (
    AgentPlanner,
    AgentExecutor,
    AgentReflector,
    AgentArchitect,
    CollaborationContext
)

logger = logging.getLogger(__name__)

class SuperBrain:
    """
    الدماغ الخارق (SuperBrain).

    يمثل "مجلس الحكماء" (Council of Wisdom) حيث تتفاعل الكيانات الذكية:
    - المخطط (Strategist): يحدد "ماذا" (What).
    - المهندس (Architect): يحدد "كيف هيكلياً" (How - Structure).
    - المنفذ (Operator): ينفذ "كيف فعلياً" (How - Action).
    - المدقق (Auditor): يضمن "الجودة والأمان" (Quality & Safety).

    يتبع مبادئ SOLID ويفصل التفكير عن إدارة الحالة.
    """

    def __init__(
        self,
        planner: AgentPlanner,
        architect: AgentArchitect,
        executor: AgentExecutor,
        reflector: AgentReflector
    ):
        self.planner = planner
        self.architect = architect
        self.executor = executor
        self.reflector = reflector

    async def think_and_plan(self, objective: str, mission_id: int) -> dict[str, Any]:
        """
        دورة التفكير والتخطيط والتصميم مع النقد الذاتي.
        Generates a plan, designs the structure, critiques, and refines.
        """
        logger.info(f"SuperBrain: Convening the council for Mission {mission_id}...")

        # إنشاء سياق التعاون
        context = CollaborationContext(mission_id=mission_id, objective=objective)

        # 1. التخطيط الاستراتيجي (Strategic Planning)
        # Strategist defines the high-level steps.
        plan = await self.planner.create_plan(objective, context)

        # 2. التصميم المعماري (Architectural Design)
        # Architect adds structural details (file paths, classes) to the plan.
        design_result = await self.architect.design_solution(plan, context)

        # Merge design into plan (or keep separate, here we enrich the plan)
        plan["design_blueprint"] = design_result.get("blueprint")

        # 3. النقد والمراجعة (Critique & Reflection)
        # Auditor reviews both the plan and the design.
        critique = await self.reflector.critique_plan(plan, objective)

        if not critique["valid"]:
            logger.warning(f"SuperBrain: Plan rejected by Auditor. Feedback: {critique['feedback']}")
            # Self-Correction Loop would go here (Re-prompt Strategist with feedback)
            # For strict MVP: we flag it.
            plan["warnings"] = critique["feedback"]
            plan["approved"] = False
        else:
            logger.info("SuperBrain: Plan and Design ratified by the Council.")
            plan["approved"] = True

        return plan

    async def execute_task_with_oversight(self, task: Any, mission_id: int = 0) -> dict[str, Any]:
        """
        تنفيذ مهمة تحت رقابة المدقق.
        Executes a task and verifies the result immediately.
        """
        logger.info(f"SuperBrain: Authorizing execution of Task {getattr(task, 'id', 'Unknown')}")

        # Context reconstruction (simplified for execution phase)
        context = CollaborationContext(
            mission_id=mission_id,
            objective=getattr(task, "objective", "Execute Task")
        )

        # 1. التنفيذ (Execution)
        result = await self.executor.execute_task(task, context)

        # 2. التحقق (Verification)
        verification = await self.reflector.verify_execution(task, result)

        if not verification["verified"]:
            logger.error(f"SuperBrain: Task verification failed! {verification['reason']}")
            result["status"] = "failed"
            result["error"] = f"Verification Failed: {verification['reason']}"

        return result
