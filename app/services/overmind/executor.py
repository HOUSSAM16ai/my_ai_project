# app/services/overmind/executor.py
# =================================================================================================
# OVERMIND EXECUTION ENGINE – HYPER-FLUX TASK RUNNER
# Version: 11.0.0-hyper-async
# =================================================================================================

import json
import logging
import asyncio
from typing import Any, Dict

from app.models import Task

logger = logging.getLogger(__name__)

# Try to import agent tools, fail gracefully
try:
    from app.services import agent_tools
except ImportError:
    agent_tools = None


class TaskExecutor:
    """
    Executes tasks using the registered Agent Tools.
    Designed for isolation and safe execution.
    """

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Executes a single task.
        Returns a dictionary with keys: status, result_text, meta, error.
        """
        tool_name = task.tool_name
        tool_args = task.tool_args_json or {}

        # Guard: Check tool availability
        if not agent_tools:
             return {
                "status": "failed",
                "error": "Agent tools registry not available."
            }

        # Standardize tool name if needed (simplified)

        try:
            # We assume agent_tools might expose a unified execute method
            # or we need to find the function in the registry.
            # Based on the original code, it seems to call internal methods.
            # Here we will try to look it up in the registry.

            registry = getattr(agent_tools, "_TOOL_REGISTRY", {})
            tool_func = registry.get(tool_name)

            if not tool_func:
                 # Fallback: Check if it's a known special tool
                 return {
                    "status": "failed",
                    "error": f"Tool '{tool_name}' not found in registry."
                }

            # Execute
            # If the tool is async, await it. If sync, run in executor.
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_args)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool_func(**tool_args))

            # Format Result
            # Tools usually return a string or a dict.
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
            return {
                "status": "failed",
                "error": str(e)
            }
