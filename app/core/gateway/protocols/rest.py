import contextlib
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from .base import ProtocolAdapter


class RESTAdapter(ProtocolAdapter):
    """REST protocol adapter"""

    async def validate_request(self, request: Request) -> tuple[bool, str | None]:
        """Validate REST request"""
        return True, None

    async def transform_request(self, request: Request) -> dict[str, Any]:
        """Transform REST request"""
        body = {}
        with contextlib.suppress(Exception):
            body = await request.json()

        return {
            "method": request.method,
            "path": request.url.path,
            "headers": dict(request.headers),
            "query": dict(request.query_params),
            "body": body,
        }

    def transform_response(self, response_data: dict[str, Any]) -> dict[str, str | int | bool]:
        """Transform to REST response"""
        return JSONResponse(content=response_data)
