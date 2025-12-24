# app/api/routers/system/__init__.py
"""
نظام التوجيه المركزي - (System Router Refactored)
طبقة العرض (Presentation Layer) التي تعتمد فقط على طبقة التطبيق (Application Layer).
يتبع مبدأ عكس التبعية (Dependency Inversion Principle) بدقة متناهية.
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.schemas.system.responses import HealthResponse, HealthzResponse, SystemInfoResponse
from app.application.interfaces import HealthCheckService, SystemService
from app.core.di import get_health_check_service, get_system_service

# إنشاء كائن الموجه (Router Instance)
router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health",
    summary="فحص صحة النظام (Application Health Check)",
    response_description="يعيد الحالة التشغيلية للتطبيق وتبعية قاعدة البيانات.",
    response_model=HealthResponse,
)
async def health_check(
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthResponse | JSONResponse:
    """
    نقطة نهاية فحص الصحة (Health Check Endpoint).
    يعتمد على واجهة الخدمة (HealthCheckService Interface) وليس التنفيذ الملموس.

    العمليات:
    1. استدعاء خدمة فحص الصحة.
    2. تحديد حالة الاستجابة (200 OK أو 503 Unavailable).
    3. إرجاع تقرير JSON مفصل.
    """
    health_data = await health_service.check_system_health()

    # التحقق من الحالة العامة
    is_healthy = health_data.get("status") == "healthy"
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    response_content = HealthResponse(
        application="ok",
        database=health_data.get("database", {}).get("status", "unknown"),
        version="v4.0-clean",
    )

    if not is_healthy:
        return JSONResponse(
            content=response_content.model_dump(),
            status_code=status_code,
        )

    return response_content


@router.get(
    "/healthz",
    summary="فحص الحيوية (Kubernetes Liveness Probe)",
    response_model=HealthzResponse,
)
async def healthz(
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> HealthzResponse | JSONResponse:
    """
    فحص بسيط لحيوية النظام (Liveness Probe) لبيئة Kubernetes.
    يتحقق فقط من القدرة على الاتصال بقاعدة البيانات.
    """
    health_data = await health_service.check_database_health()

    # إذا كان الاتصال بقاعدة البيانات ناجحاً
    if health_data.get("connected"):
        return HealthzResponse(status="ok")

    # في حالة الفشل
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=HealthzResponse(status="error", detail="Database connection failed").model_dump(),
    )


@router.get(
    "/info",
    summary="معلومات النظام (System Information)",
    response_model=SystemInfoResponse,
)
async def system_info(
    system_service: SystemService = Depends(get_system_service),
) -> dict[str, Any]:
    """
    جلب معلومات النظام الأساسية via SystemService.
    """
    # نفترض أن الخدمة تعيد قاموساً يتطابق مع SystemInfoResponse
    # أو يمكننا تحويله هنا صراحة إذا لزم الأمر
    info: dict[str, Any] = await system_service.get_system_info()
    return info
