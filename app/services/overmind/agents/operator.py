# app/services/overmind/agents/operator.py
"""
الوكيل المنفذ (Operator Agent) - الذراع الضارب.
---------------------------------------------------------
يقوم هذا الوكيل باستلام التصميم التقني وتنفيذ المهام الواحدة تلو الأخرى
باستخدام محرك التنفيذ (TaskExecutor).

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
- استخدام واجهات صارمة.
"""

import json
from typing import Any

from app.core.di import get_logger
from app.core.protocols import AgentExecutor, CollaborationContext
from app.models import Task, TaskStatus
from app.services.overmind.executor import TaskExecutor

logger = get_logger(__name__)


class OperatorAgent(AgentExecutor):
    """
    المنفذ الميداني (The Executioner).

    المسؤوليات:
    1. استلام قائمة المهام (Tasks) من التصميم.
    2. المرور على المهام وتنفيذها بالتسلسل.
    3. تسجيل نتائج التنفيذ وتمريرها للمدقق.
    """

    def __init__(self, task_executor: TaskExecutor) -> None:
        """
        تهيئة المنفذ.

        Args:
            task_executor: محرك تنفيذ المهام الفعلي.
        """
        self.executor = task_executor

    async def execute_tasks(self, design: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """
        تنفيذ المهام الواردة في التصميم.

        Args:
            design (dict): التصميم التقني المحتوي على قائمة المهام.
            context (CollaborationContext): السياق المشترك.

        Returns:
            dict: تقرير التنفيذ الشامل.
        """
        logger.info("Operator is starting execution...")

        # التحقق من وجود أخطاء في التصميم
        if "error" in design:
            logger.error(f"Operator received failed design: {design.get('error')}")
            return {
                "status": "failed",
                "tasks_executed": 0,
                "results": [],
                "error": f"Design failed: {design.get('error')}"
            }

        tasks_data = design.get("tasks", [])

        if not tasks_data:
            logger.warning("Operator received design with no tasks")
            return {
                "status": "success",
                "tasks_executed": 0,
                "results": [],
                "note": "No tasks to execute"
            }

        logger.info(f"Operator: Executing {len(tasks_data)} tasks")
        results = []
        overall_status = "success"

        for i, task_def in enumerate(tasks_data):
            task_name = task_def.get("name", f"Task-{i}")
            tool_name = task_def.get("tool_name")
            tool_args = task_def.get("tool_args", {})

            if not tool_name:
                logger.warning(f"Skipping task '{task_name}': No tool_name provided.")
                results.append({"name": task_name, "status": "skipped", "reason": "no_tool_name"})
                continue

            logger.info(f"Executing Task [{i+1}/{len(tasks_data)}]: {task_name} using {tool_name}")

            # إنشاء كائن مهمة مؤقت (Ephemeral Task Object)
            # لأن TaskExecutor يتوقع كائن Task.
            # في المستقبل قد نحدث TaskExecutor لقبول dict مباشرة.
            # ملاحظة: Task يحتاج mission_id، هنا نستخدم 0 كقيمة مؤقتة لأننا لا نملك ID المهمة مباشرة هنا
            # إلا إذا أخذناه من context.
            mission_id = context.shared_memory.get("mission_id", 0) if hasattr(context, "shared_memory") else 0

            # تحويل args إلى JSON string لأن النموذج يتوقع ذلك
            args_json = json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args)

            temp_task = Task(
                mission_id=mission_id,
                name=task_name,
                tool_name=tool_name,
                tool_args_json=args_json,
                status=TaskStatus.PENDING
            )

            # تنفيذ المهمة
            try:
                exec_result = await self.executor.execute_task(temp_task)
                logger.info(f"Task '{task_name}' completed with status: {exec_result.get('status', 'unknown')}")
            except Exception as e:
                logger.exception(f"Task '{task_name}' raised exception: {e}")
                exec_result = {
                    "status": "failed",
                    "error": f"{type(e).__name__}: {e!s}"
                }

            # تسجيل النتيجة
            results.append({
                "name": task_name,
                "tool": tool_name,
                "result": exec_result
            })

            if exec_result.get("status") == "failed":
                overall_status = "partial_failure"
                logger.warning(f"Task '{task_name}' failed: {exec_result.get('error', 'unknown error')}")
                # يمكننا هنا اتخاذ قرار بالتوقف أو الاستمرار (Fail Fast vs Continue)
                # سنستمر حالياً ولكن نسجل الفشل.

        report = {
            "status": overall_status,
            "tasks_executed": len(results),
            "results": results
        }

        # تخزين النتائج في السياق
        context.update("last_execution_report", report)
        return report
