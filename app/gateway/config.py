"""
إعدادات بوابة API (Gateway Configuration).

يحدد هذا الملف تكوين البوابة بشكل تصريحي (Data as Code).
"""

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True, slots=True)
class ServiceEndpoint:
    """
    تمثيل نقطة نهاية خدمة مصغرة.

    Attributes:
        name: اسم الخدمة الفريد
        base_url: عنوان URL الأساسي للخدمة
        health_path: مسار فحص الصحة (افتراضي: /health)
        timeout: مهلة الطلب بالثواني (افتراضي: 30)
        retry_count: عدد محاولات إعادة الطلب (افتراضي: 3)
    """

    name: str
    base_url: str
    health_path: str = "/health"
    timeout: int = 30
    retry_count: int = 3


@dataclass(frozen=True, slots=True)
class RouteRule:
    """
    قاعدة توجيه الطلبات.

    Attributes:
        path_prefix: بادئة المسار للتوجيه
        service_name: اسم الخدمة المستهدفة
        strip_prefix: إزالة البادئة قبل التوجيه (افتراضي: True)
        require_auth: يتطلب مصادقة (افتراضي: True)
    """

    path_prefix: str
    service_name: str
    strip_prefix: bool = True
    require_auth: bool = True


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    """
    تكوين البوابة الشامل.

    يتبع مبدأ "البيانات ككود" (Data as Code) من SICP.
    """

    services: tuple[ServiceEndpoint, ...] = field(default_factory=tuple)
    routes: tuple[RouteRule, ...] = field(default_factory=tuple)
    enable_cors: bool = True
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 100
    jwt_secret: str | None = None


# التكوين الافتراضي للبوابة
DEFAULT_GATEWAY_CONFIG: Final[GatewayConfig] = GatewayConfig(
    services=(
        ServiceEndpoint(
            name="planning-agent",
            base_url="http://localhost:8001",
        ),
        ServiceEndpoint(
            name="memory-agent",
            base_url="http://localhost:8002",
        ),
        ServiceEndpoint(
            name="user-service",
            base_url="http://localhost:8003",
        ),
        ServiceEndpoint(
            name="orchestrator-service",
            base_url="http://localhost:8004",
        ),
        ServiceEndpoint(
            name="observability-service",
            base_url="http://localhost:8005",
        ),
    ),
    routes=(
        RouteRule(
            path_prefix="/api/v1/planning",
            service_name="planning-agent",
        ),
        RouteRule(
            path_prefix="/api/v1/memory",
            service_name="memory-agent",
        ),
        RouteRule(
            path_prefix="/api/v1/users",
            service_name="user-service",
        ),
        RouteRule(
            path_prefix="/api/v1/orchestrator",
            service_name="orchestrator-service",
        ),
        RouteRule(
            path_prefix="/api/v1/observability",
            service_name="observability-service",
        ),
    ),
    enable_cors=True,
    enable_rate_limiting=True,
    max_requests_per_minute=100,
)
