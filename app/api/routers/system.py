# app/api/routers/system.py
"""
System-level endpoints for monitoring and health checks.
These endpoints are designed to be used by external services like
load balancers and uptime monitors.
"""

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get(
    "/health",
    summary="Application Health Check",
    response_description="Returns the operational status of the application.",
)
async def health_check():
    """
    Provides a simple health check endpoint.
    - Returns a 200 OK status if the application is running.
    - Includes a timestamp for freshness verification.
    - Designed to be lightweight for frequent polling by load balancers.
    """
    return JSONResponse(
        content={
            "status": "ok",
            "timestamp": time.time(),
        }
    )
