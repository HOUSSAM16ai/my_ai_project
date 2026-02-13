"""
Planning Agent Client.
Provides a typed interface to the Planning Agent Service.
"""

from __future__ import annotations

from typing import Final

import httpx

from app.core.http_client_factory import HTTPClientConfig, get_http_client
from app.core.logging import get_logger
from app.core.settings.base import get_settings
from app.domain.models.planning import PlanRequest, PlanResult

logger = get_logger("planning-client")

DEFAULT_PLANNING_AGENT_URL: Final[str] = "http://planning-agent:8000"


class PlanningClient:
    """
    Client for interacting with the Planning Agent microservice.
    Uses the "Contract-First" approach (Three-Plane Architecture).
    """

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        # Ensure we prioritize the specific setting, then fallback to argument or default
        resolved_url = settings.PLANNING_AGENT_URL or base_url or DEFAULT_PLANNING_AGENT_URL
        self.base_url = resolved_url.rstrip("/")
        self.config = HTTPClientConfig(
            name="planning-agent-client",
            timeout=60.0,
            max_connections=50,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        return get_http_client(self.config)

    async def generate_plan(self, goal: str, context: list[str]) -> PlanResult:
        """
        Execute plan generation via the agent's REST API.
        """
        url = f"{self.base_url}/plans"
        payload = PlanRequest(goal=goal, context=context).model_dump()

        client = await self._get_client()
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            # The API returns PlanResponse (id, goal, steps)
            # We map it to our local PlanResult
            return PlanResult(**response.json())

        except Exception as e:
            logger.error(f"Plan generation failed: {e}", exc_info=True)
            raise

    async def check_health(self) -> bool:
        """Check if the service is healthy."""
        url = f"{self.base_url}/health"
        client = await self._get_client()
        try:
            response = await client.get(url)
            return response.status_code == 200
        except Exception:
            return False


# Singleton
planning_client = PlanningClient()
