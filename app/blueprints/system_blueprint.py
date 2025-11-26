# app/blueprints/system_blueprint.py
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.blueprints import Blueprint
from app.core.database import get_db
from app.services.system_service import system_service

# Create a blueprint instance
system_blueprint = Blueprint("system")

@system_blueprint.router.get(
    "/health",
    summary="Application Health Check",
    response_description="Returns the operational status of the application and its dependencies.",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = await system_service.check_database_status(db)
    status_code = (
        status.HTTP_200_OK if db_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        content={"application": "ok", "database": db_status, "version": "v4.0-woven"},
        status_code=status_code,
    )

@system_blueprint.router.get(
    "/healthz",
    summary="Kubernetes Liveness Probe",
)
async def healthz(db: AsyncSession = Depends(get_db)):
    """Simple health check for Kubernetes liveness probes."""
    is_healthy = await system_service.is_database_connected(db)
    if is_healthy:
        return JSONResponse({"status": "ok"})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "detail": "Database connection failed"},
    )
