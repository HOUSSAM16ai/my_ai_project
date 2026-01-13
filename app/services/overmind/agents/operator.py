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

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.domain.mission import Task, TaskStatus
from app.core.protocols import AgentExecutor, CollaborationContext
from app.services.overmind.executor import TaskExecutor

logger = get_logger(__name__)


class OperatorAgent(AgentExecutor):
    """
    المنفذ الميداني (The Executioner).

    المسؤوليات:
    1. استلام قائمة المهام (Tasks) من التصميم.
    2. المرور على المهام وتنفيذها بالتسلسل.
    3. تسجيل نتائج التنفيذ وتمريرها للمدقق.
    4. تقديم استشارات حول قابلية التنفيذ والموارد.
    """

    def __init__(self, task_executor: TaskExecutor, ai_client: AIClient | None = None) -> None:
        """
        تهيئة المنفذ.

        Args:
            task_executor: محرك تنفيذ المهام الفعلي.
            ai_client: عميل الذكاء الاصطناعي (اختياري للاستشارات).
        """
        self.executor = task_executor
        self.ai = ai_client

    async def execute_tasks(
        self, design: dict[str, object], context: CollaborationContext
    ) -> dict[str, object]:
        """
        تنفيذ المهام الواردة في التصميم.
        Execute tasks from the design plan.

        Args:
            design: التصميم التقني المحتوي على قائمة المهام
            context: السياق المشترك

        Returns:
            dict: تقرير التنفيذ الشامل
        """
        logger.info("Operator is starting execution...")

        # 1. التحقق من صحة التصميم | Validate design
        validation_result = self._validate_design(design)
        if validation_result:
            return validation_result

        # 2. استخراج المهام | Extract tasks
        tasks_data = design.get("tasks", [])
        if not tasks_data:
            return self._create_empty_tasks_report()

        # 3. تنفيذ المهام | Execute tasks
        logger.info(f"Operator: Executing {len(tasks_data)} tasks")
        results, overall_status = await self._execute_task_list(tasks_data, context)

        # 4. إنشاء التقرير النهائي | Create final report
        report = self._create_execution_report(overall_status, results)
        context.update("last_execution_report", report)
        return report

    async def consult(self, situation: str, analysis: dict[str, object]) -> dict[str, object]:
        """
        تقديم استشارة حول الموقف من منظور تشغيلي.
        Provide consultation on the situation from an operational perspective.

        Args:
            situation: وصف الموقف
            analysis: تحليل الموقف

        Returns:
            dict: التوصية والثقة
        """
        logger.info("Operator is being consulted...")

        if self.ai:
            return await self._consult_with_ai(situation, analysis)

        # Fallback if no AI is available
        return {
            "recommendation": "Check system resources and task queue availability.",
            "confidence": 80.0,
        }

    async def _consult_with_ai(
        self, situation: str, analysis: dict[str, object]
    ) -> dict[str, object]:
        """
        استخدام AI لتقديم الاستشارة.
        """
        system_prompt = """
        أنت "المشغل" (The Operator)، المسؤول عن التنفيذ العملي والموارد.
        دورك هو تحليل الموقف من منظور:
        1. توافر الموارد.
        2. قابلية التنفيذ العملي.
        3. المخاطر التشغيلية.

        قدم توصية موجزة ومباشرة.
        الرد يجب أن يكون JSON فقط:
        {
            "recommendation": "string (english)",
            "confidence": float (0-100)
        }
        """

        user_message = f"Situation: {situation}\nAnalysis: {json.dumps(analysis, default=str)}"

        try:
            response_text = await self.ai.send_message(
                system_prompt=system_prompt, user_message=user_message, temperature=0.3
            )

            clean_json = self._clean_json_block(response_text)
            return json.loads(clean_json)
        except Exception as e:
            logger.warning(f"Operator consultation failed: {e}")
            return {
                "recommendation": "Proceed with caution (AI consultation failed)",
                "confidence": 50.0,
            }

    def _validate_design(self, design: dict[str, object]) -> dict[str, object] | None:
        """
        التحقق من صحة التصميم.
        Validate design for errors.

        Returns:
            dict | None: تقرير خطأ إذا كان التصميم غير صالح، None إذا كان صالحاً
        """
        if "error" in design:
            logger.error(f"Operator received failed design: {design.get('error')}")
            return {
                "status": "failed",
                "tasks_executed": 0,
                "results": [],
                "error": f"Design failed: {design.get('error')}",
            }
        return None

    def _create_empty_tasks_report(self) -> dict[str, object]:
        """
        إنشاء تقرير للتصميم بدون مهام.
        Create report for design with no tasks.
        """
        logger.warning("Operator received design with no tasks")
        return {
            "status": "success",
            "tasks_executed": 0,
            "results": [],
            "note": "No tasks to execute",
        }

    async def _execute_task_list(
        self, tasks_data: list[dict[str, object]], context: CollaborationContext
    ) -> tuple[list[dict[str, object]], str]:
        """
        تنفيذ قائمة المهام.
        Execute list of tasks sequentially.

        Returns:
            tuple: (النتائج، الحالة الإجمالية)
        """
        results = []
        overall_status = "success"

        for i, task_def in enumerate(tasks_data):
            result = await self._execute_single_task(i, task_def, tasks_data, context)
            results.append(result)

            if result.get("status") == "skipped":
                continue

            if result["result"].get("status") == "failed":
                overall_status = "partial_failure"

        return results, overall_status

    async def _execute_single_task(
        self,
        index: int,
        task_def: dict[str, object],
        tasks_data: list[dict[str, object]],
        context: CollaborationContext,
    ) -> dict[str, object]:
        """
        تنفيذ مهمة واحدة.
        Execute a single task.
        """
        task_name = task_def.get("name", f"Task-{index}")
        tool_name = task_def.get("tool_name")

        # التحقق من وجود أداة | Validate tool
        if not tool_name:
            logger.warning(f"Skipping task '{task_name}': No tool_name provided.")
            return {"name": task_name, "status": "skipped", "reason": "no_tool_name"}

        logger.info(
            f"Executing Task [{index + 1}/{len(tasks_data)}]: {task_name} using {tool_name}"
        )

        # إنشاء المهمة وتنفيذها | Create and execute task
        temp_task = self._create_task_object(task_def, context)
        exec_result = await self._execute_task_safely(temp_task, task_name)

        return {"name": task_name, "tool": tool_name, "result": exec_result}

    def _create_task_object(
        self, task_def: dict[str, object], context: CollaborationContext
    ) -> Task:
        """
        إنشاء كائن مهمة مؤقت.
        Create ephemeral task object for execution.
        """
        mission_id = self._extract_mission_id(context)
        tool_args = task_def.get("tool_args", {})
        args_json = json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args)

        return Task(
            mission_id=mission_id,
            name=task_def.get("name", "Unnamed Task"),
            tool_name=task_def.get("tool_name"),
            tool_args_json=args_json,
            status=TaskStatus.PENDING,
        )

    def _extract_mission_id(self, context: CollaborationContext) -> int:
        """
        استخراج معرف المهمة من السياق.
        Extract mission ID from context.
        """
        if hasattr(context, "shared_memory"):
            return context.shared_memory.get("mission_id", 0)
        return 0

    async def _execute_task_safely(self, task: Task, task_name: str) -> dict[str, object]:
        """
        تنفيذ المهمة مع معالجة الأخطاء.
        Execute task with error handling.
        """
        try:
            exec_result = await self.executor.execute_task(task)
            logger.info(
                f"Task '{task_name}' completed with status: {exec_result.get('status', 'unknown')}"
            )
            return exec_result
        except Exception as e:
            logger.exception(f"Task '{task_name}' raised exception: {e}")
            return {"status": "failed", "error": f"{type(e).__name__}: {e!s}"}

    def _create_execution_report(
        self, overall_status: str, results: list[dict[str, object]]
    ) -> dict[str, object]:
        """
        إنشاء تقرير التنفيذ النهائي.
        Create final execution report.
        """
        return {"status": overall_status, "tasks_executed": len(results), "results": results}

    def _clean_json_block(self, text: str) -> str:
        """استخراج JSON من نص قد يحتوي على Markdown code blocks."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
