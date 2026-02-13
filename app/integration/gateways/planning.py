from typing import Any

from app.core.logging import get_logger
from app.infrastructure.clients.planning_client import planning_client
from app.integration.protocols.planning_gateway import PlanningGatewayProtocol

logger = get_logger(__name__)


class RemotePlanningGateway(PlanningGatewayProtocol):
    """
    Remote Adapter for the Planning Agent.
    Implements the PlanningGatewayProtocol by using the HTTP Client.
    """

    async def generate_plan(
        self,
        goal: str,
        context: str = "",
    ) -> Any:
        try:
            # Convert context string to list as expected by the microservice
            context_list = [context] if context else []
            return await planning_client.generate_plan(goal, context_list)
        except Exception as e:
            logger.error(f"Error in generate_plan: {e}")
            raise


# Alias for backward compatibility if needed, but we should update imports
LocalPlanningGateway = RemotePlanningGateway
