"""
User Service Client.
Provides a typed interface to the User Service.
"""

import httpx
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger("user-client")

class UserCountResponse(BaseModel):
    count: int

class UserClient:
    """Client for interacting with the User microservice."""

    def __init__(self, base_url: str = "http://user-service:8003") -> None:
        self.base_url = base_url.rstrip("/")

    async def get_user_count(self) -> int:
        """Fetch the total number of users."""
        url = f"{self.base_url}/users/count"
        logger.info(f"Calling User Service: {url}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                data = response.json()
                return UserCountResponse(**data).count
            except httpx.HTTPError as e:
                logger.error(f"Failed to get user count: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error getting user count: {e}", exc_info=True)
                raise

# Singleton instance
user_client = UserClient()
