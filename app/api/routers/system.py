# app/api/routers/system.py
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.system_service import system_service

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
    db_status = await system_service.check_database_status(db)
    status_code = (
        status.HTTP_200_OK
        if db_status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        content={"application": "ok", "database": db_status},
        status_code=status_code,
    )


@router.get(
    "/healthz",
    summary="Kubernetes Health Check",
    tags=["System"],
)
async def healthz(db: AsyncSession = Depends(get_db)):
    """
    Simple health check endpoint for Kubernetes liveness probes.
    """
    try:
        # Simple query to check DB connection
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "detail": "Database unavailable"}
        )
