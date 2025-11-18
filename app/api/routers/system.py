# app/api/routers/system.py
"""
System-level endpoints for monitoring and health checks.
These endpoints are designed to be used by external services like
load balancers and uptime monitors.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.factories import get_db_service
from app.services.database_service import DatabaseService

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get(
    "/health",
    summary="Application Health Check",
    response_description="Returns the operational status of the application and its dependencies.",
)
async def health_check(db_service: DatabaseService = Depends(get_db_service)):
    """
    Provides a comprehensive health check endpoint.

    - Verifies the application is running.
    - **Verifies connectivity and health of the database.**
    - Returns a 200 OK status if all checks pass.
    - Returns a 503 Service Unavailable if a dependency is unhealthy.
    """
    db_health = db_service.get_database_health()

    if db_health["status"] != "healthy":
        return JSONResponse(
            content=db_health,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return JSONResponse(content=db_health, status_code=status.HTTP_200_OK)
