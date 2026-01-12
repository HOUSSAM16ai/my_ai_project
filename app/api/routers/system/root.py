"""
موجه الجذر (Root Router).

يتعامل مع نقاط النهاية الأساسية الموجودة في جذر التطبيق (مثل فحص الصحة العام).
يتبع مبادئ Clean Architecture و SOLID.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.schemas.system.responses import HealthResponse
from app.application.interfaces import HealthCheckService
from app.core.di import get_health_check_service

# موجه خاص للنقاط الجذرية (بدون بادئة)
root_router = APIRouter(tags=["Root System"])


@root_router.get(
    "/health",
    summary="فحص صحة النظام العام (General Health Check)",
    response_description="نقطة وصول سريعة لفحص حالة النظام (تستخدمها أدوات المراقبة).",
    response_model=HealthResponse,
)
async def root_health_check(
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthResponse | JSONResponse:
    """
    نقطة فحص الصحة الجذرية.

    تعتبر اسماً مستعاراً (Alias) أو نقطة وصول مباشرة لخدمة الفحص،
    متوافقة مع أدوات المراقبة القياسية التي تتوقع `/health`.
    """
    health_data = await health_service.check_system_health()
    is_healthy = health_data.get("status") == "healthy"

    response = HealthResponse(
        application="ok",
        database=health_data.get("database", {}).get("status", "unknown"),
        version="v4.1-root",
    )

    if not is_healthy:
        return JSONResponse(
            content=response.model_dump(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return response
