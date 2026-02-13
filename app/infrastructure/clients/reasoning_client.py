"""
Reasoning Agent Client.
Provides a typed interface to the Reasoning Agent Service.
"""

from __future__ import annotations

import uuid
from typing import Final

import httpx

from app.core.http_client_factory import HTTPClientConfig, get_http_client
from app.core.logging import get_logger
from app.core.settings.base import get_settings
from app.domain.models.reasoning import ReasoningNode

logger = get_logger("reasoning-client")

DEFAULT_REASONING_AGENT_URL: Final[str] = "http://reasoning-agent:8000"


class ReasoningClient:
    """
    Client for interacting with the Reasoning Agent microservice.
    Uses the "Contract-First" approach (Three-Plane Architecture).
    """

    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        resolved_url = settings.REASONING_AGENT_URL or base_url or DEFAULT_REASONING_AGENT_URL
        self.base_url = resolved_url.rstrip("/")
        self.config = HTTPClientConfig(
            name="reasoning-agent-client",
            timeout=60.0,
            max_connections=50,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        return get_http_client(self.config)

    async def execute(self, query: str, context: str) -> ReasoningNode:
        """
        Execute deep reasoning via the agent's REST API.
        """
        url = f"{self.base_url}/execute"
        payload = {
            "caller_id": "app-backend",
            "action": "reason",
            "payload": {"query": query, "context": context},
        }

        client = await self._get_client()
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise ValueError(f"Reasoning agent error: {data.get('error')}")

            result_data = data.get("data", {})

            # Map stub/result to ReasoningNode
            # If the service returns a ReasoningNode structure, we parse it directly.
            # Otherwise, we wrap the result in a node.
            if "id" in result_data and "content" in result_data:
                return ReasoningNode(**result_data)

            # Stub mapping
            return ReasoningNode(
                id=str(uuid.uuid4()),
                content=result_data.get("answer", "Reasoning completed."),
                step_type="solution",
                children=[],
            )

        except Exception as e:
            logger.error(f"Deep reasoning failed: {e}", exc_info=True)
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
reasoning_client = ReasoningClient()
