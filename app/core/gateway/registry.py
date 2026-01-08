"""
سجل بوابة الـ API (Gateway Registry).

يوفر هذا الملف كتالوجًا معلنًا للمسارات والخدمات الخلفية بحيث يمكن للبوابة
تجميعها وتوجيه الطلبات بصورة موحدة قابلة للتوسع.
"""

from app.core.gateway.models import GatewayRoute, ProtocolType, UpstreamService
from app.core.gateway.service import APIGatewayService


def _default_upstream_services() -> list[UpstreamService]:
    """
    تهيئة قائمة الخدمات الخلفية الافتراضية للبوابة.
    """
    return [
        UpstreamService(
            service_id="core-api",
            name="CogniForge Core API",
            base_url="internal://cogniforge",
            health_check_url="/api/v1/health",
            protocol=ProtocolType.REST,
            metadata={"tier": "internal"},
        ),
    ]


def _default_gateway_routes() -> list[GatewayRoute]:
    """
    تعريف المسارات القياسية للبوابة كبيانات قابلة للقراءة.
    """
    return [
        GatewayRoute(
            route_id="system-health",
            path_pattern="/api/v1/health",
            methods=["GET"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=False,
        ),
        GatewayRoute(
            route_id="database-health",
            path_pattern="/api/v1/database/health",
            methods=["GET"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=False,
        ),
        GatewayRoute(
            route_id="agents-plan",
            path_pattern="/api/v1/agents/plan",
            methods=["POST"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=True,
        ),
        GatewayRoute(
            route_id="agents-plan-fetch",
            path_pattern="/api/v1/agents/plan/{plan_id}",
            methods=["GET"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=True,
        ),
        GatewayRoute(
            route_id="overmind-missions",
            path_pattern="/api/v1/overmind/missions",
            methods=["POST"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=True,
        ),
        GatewayRoute(
            route_id="overmind-mission-detail",
            path_pattern="/api/v1/overmind/missions/{mission_id}",
            methods=["GET"],
            upstream_service="core-api",
            protocol=ProtocolType.REST,
            auth_required=True,
        ),
    ]


def register_default_gateway_catalog(gateway: APIGatewayService) -> None:
    """
    تسجيل الخدمات والمسارات الافتراضية في بوابة الـ API.
    """
    for service in _default_upstream_services():
        if service.service_id not in gateway.upstream_services:
            gateway.register_upstream_service(service)

    for route in _default_gateway_routes():
        if route.route_id not in gateway.routes:
            gateway.register_route(route)
