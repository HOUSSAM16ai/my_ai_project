"""
Readiness Gate for Overmind Services.
Ensures that critical providers are available before starting a mission.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ProviderReadinessGate:
    """
    Checks if the necessary external providers (Search, Scraping, LLM) are configured and reachable.
    """

    @staticmethod
    async def check_search_providers() -> dict[str, Any]:
        """
        Checks availability of search providers.
        Returns a status dict: {"status": "ready" | "degraded" | "failed", "details": ...}
        """
        tavily_key = os.environ.get("TAVILY_API_KEY")

        # Auto-sanitize if user accidentally pasted the MCP URL
        if tavily_key and "tavilyApiKey=" in tavily_key:
            try:
                tavily_key = tavily_key.split("tavilyApiKey=")[1].split("&")[0]
                # Log without exposing the full key
                logger.info("Auto-sanitized Tavily API Key from URL format.")
            except IndexError:
                pass

        has_tavily = bool(tavily_key and tavily_key.startswith("tvly-"))

        # Check internet egress (using a reliable endpoint like Google or Cloudflare)
        has_internet = await ProviderReadinessGate._check_egress()

        if not has_internet:
            return {
                "status": "failed",
                "reason": "No internet access (Egress blocked)",
                "details": "Cannot reach external network.",
            }

        if has_tavily:
            return {
                "status": "ready",
                "details": "Tavily API Key present.",
            }

        # Fallback to DuckDuckGo (Implicitly available via langchain community if internet works)
        # We consider this "degraded" because DDG is less reliable/powerful than Tavily for deep research.
        logger.warning(
            "Running in Degraded Mode: No Tavily API Key found. Using DuckDuckGo fallback."
        )
        return {
            "status": "degraded",
            "reason": "missing_tavily_key",
            "details": "Using DuckDuckGo fallback.",
        }

    @staticmethod
    async def _check_egress() -> bool:
        """Simple check for network connectivity."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get("https://1.1.1.1")
                return resp.status_code == 200
        except Exception:
            return False


async def check_mission_readiness() -> dict[str, Any]:
    """
    Master readiness check called before mission start.
    """
    search_status = await ProviderReadinessGate.check_search_providers()

    if search_status["status"] == "failed":
        logger.error(f"Mission Readiness Failed: {search_status}")
        return {
            "ready": False,
            "error": search_status["reason"],
        }

    if search_status["status"] == "degraded":
        logger.warning(f"Mission starting in Degraded Mode: {search_status['details']}")

    return {
        "ready": True,
        "mode": search_status["status"],
    }
