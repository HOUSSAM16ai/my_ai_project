# app/api/routers/system.py
"""
System-level endpoints for monitoring and health checks.
These endpoints are designed to be used by external services like
load balancers and uptime monitors.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get(
    "/health",
    summary="Application Health Check",
    response_description="Returns the operational status of the application and its dependencies.",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Provides a comprehensive health check endpoint.

    - Verifies the application is running.
    - **Verifies connectivity to the database.**
    - Returns a 200 OK status if all checks pass.
    - Returns a 503 Service Unavailable if a dependency is unhealthy.
    """
    try:
        # A simple query to check database connectivity.
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
        status_code = status.HTTP_200_OK
    except Exception:
        db_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content={"application": "ok", "database": db_status},
        status_code=status_code,
    )
