# app/api/routers/system/__init__.py
"""
نظام التوجيه المركزي - (System Router Refactored)

هذه الوحدة تمثل طبقة العرض (Presentation Layer) لمسارات النظام.
تتبع معايير CS50 2025 في الصرامة:
1. عكس التبعية (Dependency Inversion).
2. الكتابة الصارمة (Strict Typing).
3. التوثيق الشامل (Comprehensive Documentation).
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.application.interfaces import HealthCheckService, SystemService
from app.core.di import get_health_check_service, get_system_service

__all__ = ["router"]

# إنشاء كائن الموجه (Router Instance)
router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health",
    summary="فحص صحة النظام (Application Health Check)",
    response_description="يعيد الحالة التشغيلية للتطبيق وتبعية قاعدة البيانات.",
)
async def health_check(
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> JSONResponse:
    """
    نقطة نهاية فحص الصحة (Health Check Endpoint).

    تقوم هذه الدالة بفحص صحة النظام الشاملة، بما في ذلك الاتصال بقاعدة البيانات.
    تعتمد على `HealthCheckService` المحقونة للحصول على البيانات.

    Args:
        health_service (HealthCheckService): خدمة فحص الصحة (محقونة).

    Returns:
        JSONResponse: تقرير JSON بحالة النظام (200 OK أو 503 Unavailable).
    """
    health_data: dict[str, Any] = await health_service.check_system_health()

    # التحقق من الحالة العامة
    is_healthy: bool = health_data.get("status") == "healthy"
    status_code: int = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content={
            "application": "ok",
            "database": health_data.get("database", {}).get("status", "unknown"),
            "version": "v4.0-clean",
        },
        status_code=status_code,
    )


@router.get(
    "/healthz",
    summary="فحص الحيوية (Kubernetes Liveness Probe)",
)
async def healthz(
    health_service: HealthCheckService = Depends(get_health_check_service),
) -> JSONResponse:
    """
    فحص بسيط لحيوية النظام (Liveness Probe) لبيئة Kubernetes.

    يتحقق فقط من القدرة على الاتصال بقاعدة البيانات لضمان أن الحاوية "حية".

    Args:
        health_service (HealthCheckService): خدمة فحص الصحة (محقونة).

    Returns:
        JSONResponse: 'ok' إذا كانت قاعدة البيانات متصلة، وإلا 503.
    """
    health_data: dict[str, Any] = await health_service.check_database_health()

    # إذا كان الاتصال بقاعدة البيانات ناجحاً
    if health_data.get("connected"):
        return JSONResponse({"status": "ok"})

    # في حالة الفشل
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "detail": "Database connection failed"},
    )


@router.get(
    "/info",
    summary="معلومات النظام (System Information)",
)
async def system_info(
    system_service: SystemService = Depends(get_system_service),
) -> JSONResponse:
    """
    جلب معلومات النظام الأساسية.

    Args:
        system_service (SystemService): خدمة النظام (محقونة).

    Returns:
        JSONResponse: معلومات النظام (إصدار، بيئة، إلخ).
    """
    info: dict[str, Any] = await system_service.get_system_info()
    return JSONResponse(content=info)
