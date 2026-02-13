from typing import Any

from app.core.integration_kernel.contracts import ActionEngine
from app.core.integration_kernel.ir import AgentAction
from app.core.logging import get_logger

logger = get_logger(__name__)


class KagentDriver(ActionEngine):
    """
    Driver for executing actions using Kagent.
    """

    async def execute(self, action: AgentAction) -> dict[str, Any]:
        """
        Executes a defined action via KagentMesh.
        """
        try:
            from app.services.kagent import AgentRequest, KagentMesh

            mesh = KagentMesh()
            request = AgentRequest(
                action=action.action_name,
                capability=action.capability,
                payload=action.payload or {},
            )

            response = await mesh.execute_action(request)

            return {
                "success": response.success,
                "result": response.result,
                "error": response.error,
            }
        except Exception as e:
            logger.error(f"Kagent execution error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """
        Returns the health status of the Kagent engine.
        """
        try:
            from app.services.kagent import KagentMesh  # noqa: F401

            return {
                "status": "active",
                "components": ["ServiceRegistry", "SecurityMesh", "LocalAdapter"],
            }
        except ImportError:
            return {"status": "unavailable", "error": "Kagent module missing"}
