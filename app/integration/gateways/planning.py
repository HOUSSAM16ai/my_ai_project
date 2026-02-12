from typing import Any

from app.core.logging import get_logger
from app.integration.protocols.planning_gateway import PlanningGatewayProtocol

logger = get_logger(__name__)

class LocalPlanningGateway(PlanningGatewayProtocol):
    """
    Local Adapter for the Planning Agent.
    Implements the PlanningGatewayProtocol by directly importing the microservice code.
    """

    async def generate_plan(
        self,
        goal: str,
        context: str = "",
    ) -> Any:
        try:
            from microservices.planning_agent.cognitive import PlanGenerator

            generator = PlanGenerator()
            return generator.forward(goal=goal, context=context)
        except ImportError as e:
            logger.error(f"Planning Agent module not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in generate_plan: {e}")
            raise
