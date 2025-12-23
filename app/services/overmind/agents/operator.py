# app/services/overmind/agents/operator.py
import logging
from typing import Any
from app.core.protocols import AgentExecutor, ToolRegistryProtocol, CollaborationContext

logger = logging.getLogger(__name__)

class OperatorAgent(AgentExecutor):
    """
    المنفذ التشغيلي (Operator Agent).
    الذراع الضاربة للنظام. يقوم بتنفيذ المهام باستخدام الأدوات المتاحة بدقة متناهية.
    "الأفعال أبلغ من الأقوال."
    """

    def __init__(self, tool_registry: ToolRegistryProtocol):
        self.tools = tool_registry

    @property
    def name(self) -> str:
        return "Operator (Omega-Red)"

    async def execute_task(self, task: Any, context: CollaborationContext | None = None) -> dict[str, Any]:
        """
        Executes a single task.
        Expected task object to have 'tool_name' and 'parameters'.
        """
        # Handling different task structures (Pydantic model vs Dict)
        tool_name = getattr(task, "tool_name", None) or (task.get("tool_name") if isinstance(task, dict) else None)
        params = getattr(task, "parameters", None) or (task.get("parameters", {}) if isinstance(task, dict) else {})

        if not tool_name:
            return {"status": "failed", "error": "No tool specified"}

        logger.info(f"Operator: Engaging tool '{tool_name}' with params: {params}")

        tool = self.tools.get(tool_name)
        if not tool:
            logger.error(f"Operator: Tool '{tool_name}' not found in registry.")
            return {"status": "failed", "error": f"Tool '{tool_name}' not found"}

        try:
            # Execute the tool
            result = await tool.execute(**params)

            result_data = {
                "status": "success",
                "result_text": str(result),
                "meta": {"tool": tool_name}
            }

            # If context is provided, we could log the execution there
            if context:
                # Example: context.add_artifact(f"execution_{task.id}", result)
                pass

            logger.info(f"Operator: Tool '{tool_name}' execution successful.")
            return result_data

        except Exception as e:
            logger.exception(f"Operator: Execution failed for tool '{tool_name}'")
            return {
                "status": "failed",
                "error": str(e),
                "meta": {"tool": tool_name}
            }
