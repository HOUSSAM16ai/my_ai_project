"""
Superhuman Security

هذا الملف جزء من مشروع CogniForge.
"""

# app/middleware/superhuman_security.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.security.waf import waf


class SuperhumanSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            await waf.check_request(request)
            # The rate limiter is now a dependency, so it's not called here
            # await rate_limiter(request)
        except Exception as e:
            if hasattr(e, "status_code"):
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                )
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal security error occurred."},
            )

        response = await call_next(request)
        return response
