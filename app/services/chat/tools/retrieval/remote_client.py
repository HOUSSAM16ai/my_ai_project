"""
Remote Memory Agent Client.
Infrastructure Layer.
"""

import os
from typing import Any

import httpx

from app.core.logging import get_logger

logger = get_logger("tool-retrieval-remote")


async def fetch_from_memory_agent(query: str, tags: list[str]) -> list[dict[str, Any]]:
    """
    Fetches content from the Memory Agent microservice.
    Returns a list of result dictionaries or raises an exception/returns empty on failure.
    """
    # Default to Memory Agent URL or localhost for dev
    memory_url = os.getenv("MEMORY_AGENT_URL") or "http://memory-agent:8002"
    search_url = f"{memory_url}/memories/search"

    logger.info(f"Searching content with query='{query}' and tags={tags}")

    search_payload = {
        "query": query,
        "filters": {"tags": tags},
        "limit": 5,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(search_url, json=search_payload)
        response.raise_for_status()

        results = response.json()
        if not results or not isinstance(results, list):
            return []

        return results
