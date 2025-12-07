from typing import Any

from fastapi import Request

from .base import ProtocolAdapter


class GRPCAdapter(ProtocolAdapter):
    """gRPC protocol adapter (placeholder for future implementation)"""

    async def validate_request(self, request: Request) -> tuple[bool, str | None]:
        """Validate gRPC request"""
        return True, None

    async def transform_request(self, request: Request) -> dict[str, Any]:
        """Transform gRPC request"""
        return {"metadata": {"protocol": "grpc"}}

    def transform_response(self, response_data: dict[str, Any]) -> Any:
        """Transform to gRPC response"""
        return response_data
