from typing import Any

from app.core.logging import get_logger
from app.services.chat.agents.base import AgentResponse

logger = get_logger("data-access-agent")

class DataAccessAgent:
    """
    Ensures correct service ownership and DB interactions.
    """

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Checks if the data access is routed to the correct microservice.
        """
        entity = input_data.get("entity")
        operation = input_data.get("operation")

        logger.info(f"Checking data access for {entity}::{operation}")

        if entity == "user":
            # Enforce that User data must be accessed via User Service
            if input_data.get("access_method") == "direct_db":
                return AgentResponse(success=False, message="User data must be accessed via User Service API, not direct DB.")
            return AgentResponse(success=True, message="User access routed correctly.")

        return AgentResponse(success=True, message="Data access check passed.")
