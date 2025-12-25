"""
محرك التنفيذ (Task Executor).
الذراع التنفيذي للنظام (The Hands).

المعايير:
- CS50 2025: توثيق عربي، صرامة في النوع.
- Dependency Injection: يعتمد على السجل (Registry) ومدير الحالة (State).
"""

import asyncio
import json
import logging
from typing import Any

from app.models import Task

# استيراد بروتوكول السجل إذا كان موجوداً، أو استخدام Any مؤقتاً
# سنستخدم Any للسجل حالياً لتجنب التعقيد، مع الافتراض أنه قاموس
from app.services.overmind.state import MissionStateManager

logger = logging.getLogger(__name__)

__all__ = ["TaskExecutor"]


class TaskExecutor:
    """
    منفذ المهام.
    مسؤول عن استدعاء الأدوات وتشغيلها في بيئة آمنة.
    """

    def __init__(self, state_manager: MissionStateManager) -> None:
        """
        تهيئة المنفذ.

        Args:
            state_manager (MissionStateManager): مدير الحالة (لتسجيل النتائج الجزئية إذا لزم الأمر).
        """
        self.state_manager = state_manager

        # محاولة الوصول إلى سجل الأدوات.
        # في التصميم المثالي، يجب حقن السجل هنا.
        # للتوافق السريع، سنحاول استيراده.
        try:
            from app.services import agent_tools
            self.registry = getattr(agent_tools, "_TOOL_REGISTRY", {})
        except ImportError:
            logger.warning("Agent tools registry not available.")
            self.registry = {}

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        تنفيذ مهمة واحدة باستخدام الأداة المحددة.

        Args:
            task (Task): كائن المهمة.

        Returns:
            dict[str, Any]: نتيجة التنفيذ (status, result_text, meta, error).
        """
        tool_name = task.tool_name
        # التعامل الآمن مع JSON
        if isinstance(task.tool_args_json, str):
            try:
                tool_args = json.loads(task.tool_args_json)
            except json.JSONDecodeError:
                tool_args = {}
        else:
            tool_args = task.tool_args_json or {}

        # 1. التحقق من وجود السجل
        if not self.registry:
            return {"status": "failed", "error": "Agent tools registry not available."}

        try:
            # 2. البحث عن الأداة
            tool_func = self.registry.get(tool_name)

            if not tool_func:
                return {"status": "failed", "error": f"Tool '{tool_name}' not found in registry."}

            # 3. التنفيذ (Execution)
            # دعم الأدوات المتزامنة وغير المتزامنة
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_args)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool_func(**tool_args))

            # 4. تنسيق النتيجة
            result_text = str(result)
            if isinstance(result, dict):
                result_text = json.dumps(result, default=str)

            return {"status": "success", "result_text": result_text, "meta": {"tool": tool_name}}

        except Exception as e:
            logger.error(f"Task Execution Error ({tool_name}): {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
