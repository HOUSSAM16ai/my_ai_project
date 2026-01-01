"""
Health check endpoints.
"""

import time

from fastapi import APIRouter

from app.api.v2.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()

@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Complexity: 1
    """
    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        uptime=uptime,
        services={
            "chat": "operational",
            "tools": "operational",
            "database": "operational",
        },
    )

@router.get("/ready")
async def readiness_check() -> dict:
    """
    Readiness check for Kubernetes.

    Complexity: 1
    """
    return {"ready": True}

@router.get("/live")
async def liveness_check() -> dict:
    """
    Liveness check for Kubernetes.

    Complexity: 1
    """
    return {"alive": True}
