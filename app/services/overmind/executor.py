"""
محرك التنفيذ (Task Executor).
الذراع التنفيذي للنظام (The Hands).

المعايير:
- CS50 2025: توثيق عربي، صرامة في النوع.
- Dependency Injection: يعتمد على السجل (Registry) ومدير الحالة (State).
- SICP: Abstraction Barriers (لا يعرف تفاصيل التسجيل، فقط يستقبله).
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.models import Task
from app.services.overmind.state import MissionStateManager

logger = logging.getLogger(__name__)

__all__ = ["TaskExecutor"]

# تعريف نوع السجل: قاموس يربط الاسم بدالة (متزامنة أو غير متزامنة)
type ToolRegistry = dict[str, Callable[..., Awaitable[Any] | Any]]


class TaskExecutor:
    """
    منفذ المهام.
    مسؤول عن استدعاء الأدوات وتشغيلها في بيئة آمنة.
    """

    def __init__(
        self,
        state_manager: MissionStateManager,
        registry: ToolRegistry
    ) -> None:
        """
        تهيئة المنفذ.

        Args:
            state_manager (MissionStateManager): مدير الحالة (لتسجيل النتائج الجزئية إذا لزم الأمر).
            registry (ToolRegistry): سجل الأدوات المحقون (Dependency Injection).
        """
        self.state_manager = state_manager
        self.registry = registry

        if not self.registry:
            logger.warning("TaskExecutor initialized with empty registry.")

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        تنفيذ مهمة واحدة باستخدام الأداة المحددة.

        Args:
            task (Task): كائن المهمة.

        Returns:
            dict[str, Any]: نتيجة التنفيذ (status, result_text, meta, error).
        """
        tool_name = task.tool_name
        tool_args = self._parse_args(task.tool_args_json)

        # 1. التحقق من وجود السجل
        if not self.registry:
            return {"status": "failed", "error": "Agent tools registry is empty."}

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

    def _parse_args(self, args_json: str | dict | None) -> dict[str, Any]:
        """
        تحليل وسائط الأداة بشكل آمن.

        Args:
            args_json: سلسلة نصية JSON أو قاموس أو None.

        Returns:
            dict: قاموس الوسائط.
        """
        if args_json is None:
            return {}
        if isinstance(args_json, dict):
            return args_json
        try:
            return json.loads(args_json)
        except json.JSONDecodeError:
            logger.warning("Failed to decode tool arguments JSON.")
            return {}
