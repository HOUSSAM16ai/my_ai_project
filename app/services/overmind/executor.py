# app/services/overmind/executor.py
# =================================================================================================
# OVERMIND EXECUTION ENGINE – HYPER-FLUX TASK RUNNER
# Version: 12.0.0-solid-refactor
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
    Executes tasks using the registered Agent Tools.
    Designed for isolation and safe execution.
    Adheres to SOLID principles by using the ToolRegistryProtocol.
    """

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        Executes a single task.
        Returns a dictionary with keys: status, result_text, meta, error.
        """
        tool_name = task.tool_name
        tool_args = task.tool_args_json or {}

        try:
            registry = get_registry()
            tool = registry.get(tool_name)

            if not tool:
                return {
                    "status": "failed",
                    "error": f"Tool '{tool_name}' not found in registry."
                }

            # Execute via the Tool Protocol
            result = await tool.execute(**tool_args)

            # Format Result
            result_text = str(result)
            if isinstance(result, dict):
                result_text = json.dumps(result, default=str)

            return {
                "status": "success",
                "result_text": result_text,
                "meta": {"tool": tool_name}
            }

        except Exception as e:
            logger.error(f"Task Execution Error ({tool_name}): {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
