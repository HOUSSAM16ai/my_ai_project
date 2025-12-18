# app/blueprints/system_blueprint.py
"""
System Blueprint - Refactored for Clean Architecture
Presentation layer that depends only on Application layer (not Infrastructure).
Follows Dependency Inversion Principle.
"""
from fastapi import Depends, status
from fastapi.responses import JSONResponse

from app.application.interfaces import HealthCheckService, SystemService
from app.blueprints import Blueprint
from app.core.di import get_health_check_service, get_system_service

# Create a blueprint instance
system_blueprint = Blueprint("system")


@system_blueprint.router.get(
    "/health",
    summary="Application Health Check",
    response_description="Returns the operational status of the application and its dependencies.",
)
async def health_check(
    health_service: HealthCheckService = Depends(get_health_check_service),
):
    """
    Health check endpoint.
    Depends on HealthCheckService interface (DIP), not concrete implementation.
    """
    health_data = await health_service.check_system_health()
    status_code = (
        status.HTTP_200_OK
        if health_data["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        content={
            "application": "ok",
            "database": health_data["database"]["status"],
            "version": "v4.0-clean",
        },
        status_code=status_code,
    )


@system_blueprint.router.get(
    "/healthz",
    summary="Kubernetes Liveness Probe",
)
async def healthz(
    health_service: HealthCheckService = Depends(get_health_check_service),
):
    """
    Simple health check for Kubernetes liveness probes.
    Depends on HealthCheckService interface (DIP).
    """
    health_data = await health_service.check_database_health()
    if health_data["connected"]:
        return JSONResponse({"status": "ok"})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "detail": "Database connection failed"},
    )


@system_blueprint.router.get(
    "/info",
    summary="System Information",
)
async def system_info(
    system_service: SystemService = Depends(get_system_service),
):
    """
    Get system information.
    Depends on SystemService interface (DIP).
    """
    info = await system_service.get_system_info()
    return JSONResponse(content=info)
