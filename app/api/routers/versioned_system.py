"""
موجه النظام المُنسخ (Versioned System Router).

يوفر واجهات v1 العامة لفحص الصحة بما يتوافق مع متطلبات البوابة والإصدار.
"""

from fastapi import APIRouter, Depends, Response, status

from app.api.schemas.system.responses import DatabaseHealth, HealthResponse
from app.application.interfaces import HealthCheckService
from app.core.di import get_health_check_service

router = APIRouter(prefix="/api/v1", tags=["System v1"])


@router.get(
    "/health",
    summary="فحص صحة النظام العام (v1)",
    response_model=HealthResponse,
)
async def versioned_health_check(
    response: Response,
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthResponse:
    """
    نقطة فحص صحة النظام بنسخة v1 للاستخدام عبر بوابة الـ API.
    """
    health_data = await health_service.check_system_health()
    is_healthy = health_data.get("status") == "healthy"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        application="ok",
        database=health_data.get("database", {}).get("status", "unknown"),
        version="v1",
    )


@router.get(
    "/database/health",
    summary="فحص صحة قاعدة البيانات (v1)",
    response_model=DatabaseHealth,
)
async def versioned_database_health(
    response: Response,
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> DatabaseHealth:
    """
    يعيد حالة الاتصال بقاعدة البيانات ضمن عقد v1 موحد.
    """
    db_health = await health_service.check_database_health()
    is_connected = db_health.get("connected") is True

    if not is_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return DatabaseHealth(
        status=db_health.get("status", "unknown"),
        detail=db_health.get("error"),
    )
