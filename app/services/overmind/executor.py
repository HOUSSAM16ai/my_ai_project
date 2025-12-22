# app/services/overmind/executor.py
# =================================================================================================
# OVERMIND EXECUTION ENGINE – HYPER-FLUX TASK RUNNER (الذراع المنفذة)
# Version: 13.0.0-super-executor
# =================================================================================================

import asyncio
import json
import logging
from typing import Any

from app.models import Task
from app.services.agent_tools.infrastructure.registry import get_registry

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    الذراع المنفذة (Task Executor).

    هذا الكلاس هو "عضلات" النظام. يتلقى الأوامر من العقل المدبر وينفذها بدقة متناهية
    باستخدام الأدوات المسجلة في النظام.

    كيف يعمل؟
    1. يستلم المهمة (Task) التي تحتوي على اسم الأداة والمدخلات.
    2. يبحث عن الأداة في "صندوق الأدوات" (Tool Registry).
    3. ينفذ الأداة ويعيد النتيجة.
    """

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        تنفيذ مهمة واحدة باستخدام الأداة المناسبة.

        Args:
            task: كائن المهمة الذي يحتوي على اسم الأداة والبيانات.

        Returns:
            dict: نتيجة التنفيذ (نجاح/فشل، والبيانات الناتجة).
        """
        tool_name = task.tool_name
        tool_args = task.tool_args_json or {}

        logger.info(f"Executor: Running tool '{tool_name}' for task {task.id}...")

        try:
            # 1. جلب الأداة من السجل
            registry = get_registry()
            tool = registry.get(tool_name)

            if not tool:
                logger.error(f"Executor: Tool '{tool_name}' is missing!")
                return {
                    "status": "failed",
                    "error": f"Tool '{tool_name}' not found in registry (Did you register it?)."
                }

            # 2. التنفيذ الفعلي (اللحظة الحاسمة)
            # ندعم التنفيذ المتزامن وغير المتزامن بشفافية
            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**tool_args)
            else:
                # إذا كانت الأداة متزامنة (Sync)، نشغلها في ThreadPool لعدم تعطيل النظام
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool.execute(**tool_args))

            # 3. تنسيق النتيجة
            result_text = str(result)
            if isinstance(result, (dict, list)):
                result_text = json.dumps(result, default=str, ensure_ascii=False)

            logger.info(f"Executor: Tool '{tool_name}' finished successfully.")
            return {
                "status": "success",
                "result_text": result_text,
                "meta": {"tool": tool_name}
            }

        except Exception as e:
            logger.error(f"Executor: Fatal error in tool '{tool_name}': {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
