import httpx
from typing import Optional, Dict, Any
from app.core.interfaces.services import IReasoningService
from app.core.logging import get_logger

logger = get_logger(__name__)

class HttpReasoningClient(IReasoningService):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def reason(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload = {
                "query": query,
                # Context integration if supported by agent
            }
            response = await self.client.post("/execute", json={
                "caller_id": "app-core",
                "target_service": "reasoning_agent",
                "action": "reason",
                "payload": payload
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise RuntimeError(data.get("error"))

            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to execute reasoning: {e}")
            raise

    async def close(self):
        await self.client.aclose()
