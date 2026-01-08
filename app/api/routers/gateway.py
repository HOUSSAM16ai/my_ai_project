"""
موجه بوابة الـ API الموحدة.

يوفر نقاط نهاية لإدارة بوابة الـ API، وتوثيق المسارات المسجلة،
وتقديم مؤشرات صحة موحدة ضمن الإصدار v1.
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas.gateway import (
    GatewayHealthResponse,
    GatewayRouteResponse,
    GatewayRoutesResponse,
    GatewayStatsResponse,
)
from app.core.gateway.registry import register_default_gateway_catalog
from app.core.gateway.service import APIGatewayService

router = APIRouter(prefix="/api/v1/gateway", tags=["API Gateway"])


def _ensure_gateway_catalog(gateway: APIGatewayService) -> None:
    """
    ضمان تسجيل كتالوج البوابة الافتراضي مرة واحدة.
    """
    register_default_gateway_catalog(gateway)

def get_gateway_from_state(request: Request) -> APIGatewayService:
    """
    الحصول على بوابة الـ API من حالة التطبيق.
    """
    gateway = getattr(request.app.state, "api_gateway", None)
    if gateway is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API gateway is not initialized",
        )
    return gateway


@router.get(
    "/health",
    summary="فحص صحة بوابة الـ API",
    response_model=GatewayHealthResponse,
)
async def gateway_health(
    gateway: APIGatewayService = Depends(get_gateway_from_state),
) -> GatewayHealthResponse:
    """
    يعيد ملخصًا سريعًا عن حالة البوابة وعدد المسارات والخدمات المسجلة.
    """
    _ensure_gateway_catalog(gateway)
    stats = gateway.get_gateway_stats()
    return GatewayHealthResponse(
        status="ok",
        version="v1",
        routes_registered=stats["routes_registered"],
        upstream_services=stats["upstream_services"],
        protocols=stats["protocols_supported"],
    )


@router.get(
    "/routes",
    summary="استعراض مسارات بوابة الـ API",
    response_model=GatewayRoutesResponse,
)
async def gateway_routes(
    gateway: APIGatewayService = Depends(get_gateway_from_state),
) -> GatewayRoutesResponse:
    """
    يعيد جميع المسارات المسجلة في البوابة بصيغة قابلة للتوثيق.
    """
    _ensure_gateway_catalog(gateway)
    routes = [
        GatewayRouteResponse(
            **{
                **asdict(route),
                "protocol": route.protocol.value,
                "metadata": {str(k): str(v) for k, v in route.metadata.items()},
            }
        )
        for route in gateway.routes.values()
    ]
    return GatewayRoutesResponse(routes=routes)


@router.get(
    "/stats",
    summary="إحصاءات بوابة الـ API",
    response_model=GatewayStatsResponse,
)
async def gateway_stats(
    gateway: APIGatewayService = Depends(get_gateway_from_state),
) -> GatewayStatsResponse:
    """
    يعيد إحصاءات تفصيلية عن حالة البوابة والتخزين المؤقت والسياسات.
    """
    _ensure_gateway_catalog(gateway)
    stats = gateway.get_gateway_stats()
    return GatewayStatsResponse(
        routes_registered=stats["routes_registered"],
        upstream_services=stats["upstream_services"],
        cache_stats=stats["cache_stats"],
        policy_violations=stats["policy_violations"],
        protocols_supported=stats["protocols_supported"],
    )
