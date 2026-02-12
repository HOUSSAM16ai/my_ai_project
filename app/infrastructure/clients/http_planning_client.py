import httpx
from typing import List, Optional
from app.core.interfaces.services import IPlanningService
from app.domain.models.agents import Plan
from app.core.logging import get_logger

logger = get_logger(__name__)

class HttpPlanningClient(IPlanningService):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def generate_plan(self, goal: str, context: Optional[List[str]] = None) -> Plan:
        try:
            # The Planning Agent has a specific /plans endpoint
            payload = {
                "goal": goal,
                "context": context or []
            }
            response = await self.client.post("/plans", json=payload)
            response.raise_for_status()
            data = response.json()

            # Map response to Plan model
            return Plan(**data)

        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise

    async def close(self):
        await self.client.aclose()
