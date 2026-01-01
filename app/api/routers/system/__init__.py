# app/api/routers/system/__init__.py
"""
نظام التوجيه المركزي - (System Router Package)
يجمع كافة موجهات النظام الفرعية ويصدرها كواجهة موحدة.
"""

from fastapi import APIRouter, Depends, Response, status

from app.api.routers.system.root import root_router
from app.api.schemas.system.responses import HealthResponse, HealthzResponse, SystemInfoResponse
from app.application.interfaces import HealthCheckService, SystemService
from app.core.di import get_health_check_service, get_system_service

# تصدير root_router لاستخدامه في Kernel
__all__ = ["root_router", "router"]

# إنشاء كائن الموجه (Router Instance) - النطاق الفرعي
router = APIRouter(prefix="/system", tags=["System"])

@router.get(
    "/health",
    summary="فحص صحة النظام (Application Health Check)",
    response_description="يعيد الحالة التشغيلية للتطبيق وتبعية قاعدة البيانات.",
    response_model=HealthResponse,
)
async def health_check(
    response: Response,
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthResponse:
    """
    نقطة نهاية فحص الصحة (Health Check Endpoint).
    يعتمد على واجهة الخدمة (HealthCheckService Interface) وليس التنفيذ الملموس.
    """
    health_data = await health_service.check_system_health()

    # التحقق من الحالة العامة
    is_healthy = health_data.get("status") == "healthy"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        application="ok",
        database=health_data.get("database", {}).get("status", "unknown"),
        version="v4.0-clean",
    )

@router.get(
    "/healthz",
    summary="فحص الحيوية (Kubernetes Liveness Probe)",
    response_model=HealthzResponse,
)
async def healthz(
    response: Response,
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthzResponse:
    """
    فحص بسيط لحيوية النظام (Liveness Probe) لبيئة Kubernetes.
    يتحقق فقط من القدرة على الاتصال بقاعدة البيانات.
    """
    health_data = await health_service.check_database_health()

    if health_data.get("connected"):
        return HealthzResponse(status="ok")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthzResponse(status="error", detail="Database connection failed")

@router.get(
    "/info",
    summary="معلومات النظام (System Information)",
    response_model=SystemInfoResponse,
)
async def system_info(
    system_service: SystemService = Depends(get_system_service),
) -> SystemInfoResponse:
    """
    جلب معلومات النظام الأساسية.
    """
    info: dict[str, Any] = await system_service.get_system_info()
    return SystemInfoResponse.model_validate(info)
