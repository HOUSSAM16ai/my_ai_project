from abc import ABC, abstractmethod
from typing import Any

from fastapi import Request


class ProtocolAdapter(ABC):
    """Abstract protocol adapter interface"""

    @abstractmethod
    async def validate_request(self, request: Request) -> tuple[bool, str | None]:
        """Validate request format"""
        pass

    @abstractmethod
    async def transform_request(self, request: Request) -> dict[str, Any]:
        """Transform request to internal format"""
        pass

    @abstractmethod
    def transform_response(self, response_data: dict[str, Any]) -> Any:
        """Transform internal format to protocol format"""
        pass
