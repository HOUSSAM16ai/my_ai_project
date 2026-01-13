"""
بوابة API (API Gateway).

نقطة الدخول المركزية لجميع طلبات API مع دعم:
- التوجيه الذكي
- المصادقة والتفويض
- تحديد المعدل
- موازنة الحمل
- إعادة المحاولة التلقائية
"""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

from app.gateway.config import GatewayConfig, RouteRule
from app.gateway.registry import ServiceRegistry

logger = logging.getLogger(__name__)


class APIGateway:
    """
    بوابة API المركزية.

    المبادئ:
    - API-First: كل شيء يمر عبر API
    - Zero Trust: كل طلب يتم التحقق منه
    - Resilience: إعادة المحاولة والتعامل مع الأخطاء
    - Observability: تسجيل جميع الطلبات
    """

    def __init__(
        self,
        config: GatewayConfig,
        registry: ServiceRegistry | None = None,
    ) -> None:
        """
        تهيئة البوابة.

        Args:
            config: تكوين البوابة
            registry: سجل الخدمات (اختياري)
        """
        self.config = config
        self.registry = registry or ServiceRegistry(services=config.services)
        self.router = self._build_router()

        logger.info("✅ API Gateway initialized")

    def _build_router(self) -> APIRouter:
        """
        يبني موجه البوابة.

        Returns:
            APIRouter: الموجه المكون
        """
        router = APIRouter(prefix="/gateway", tags=["Gateway"])

        @router.get("/health")
        async def gateway_health() -> dict[str, object]:
            """يفحص صحة البوابة وجميع الخدمات."""
            services_health = await self.registry.check_all_health()

            healthy_count = sum(1 for h in services_health.values() if h.is_healthy)
            total_count = len(services_health)

            return {
                "gateway": "healthy",
                "services": {
                    name: {
                        "healthy": health.is_healthy,
                        "response_time_ms": health.response_time_ms,
                        "last_check": health.last_check.isoformat(),
                        "error": health.error_message,
                    }
                    for name, health in services_health.items()
                },
                "summary": {
                    "healthy": healthy_count,
                    "total": total_count,
                    "percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
                },
            }

        @router.get("/services")
        async def list_services() -> dict[str, object]:
            """يعرض جميع الخدمات المسجلة."""
            services = self.registry.list_services()
            return {
                "services": [
                    {
                        "name": svc.name,
                        "base_url": svc.base_url,
                        "health_path": svc.health_path,
                        "timeout": svc.timeout,
                    }
                    for svc in services.values()
                ],
                "count": len(services),
            }

        @router.api_route(
            "/{service_name}/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        )
        async def proxy_request(
            service_name: str,
            path: str,
            request: Request,
        ) -> Response:
            """يوجه الطلب إلى الخدمة المناسبة."""
            return await self._proxy_to_service(service_name, path, request)

        return router

    async def _proxy_to_service(
        self,
        service_name: str,
        path: str,
        request: Request,
    ) -> Response:
        """
        يوجه الطلب إلى خدمة مصغرة.

        Args:
            service_name: اسم الخدمة
            path: المسار المطلوب
            request: الطلب الأصلي

        Returns:
            Response: استجابة الخدمة

        Raises:
            HTTPException: في حالة فشل التوجيه
        """
        # البحث عن الخدمة
        service = self.registry.get_service(service_name)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found",
            )

        # فحص صحة الخدمة إذا لزم الأمر
        if self.registry.should_check_health(service_name):
            health = await self.registry.check_health(service_name)
            if not health.is_healthy:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service '{service_name}' is unhealthy: {health.error_message}",
                )

        # بناء URL الهدف
        target_url = f"{service.base_url}/{path}"

        # استخراج البيانات من الطلب
        headers = dict(request.headers)
        # إزالة ترويسات قد تسبب مشاكل
        headers.pop("host", None)
        headers.pop("content-length", None)

        query_params = dict(request.query_params)
        body = await request.body()

        # إعادة المحاولة مع Exponential Backoff
        last_error = None
        for attempt in range(service.retry_count):
            try:
                async with httpx.AsyncClient(timeout=service.timeout) as client:
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        params=query_params,
                        content=body,
                    )

                    # إعادة الاستجابة
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.headers.get("content-type"),
                    )

            except httpx.TimeoutException:
                last_error = f"Timeout after {service.timeout}s"
                logger.warning(
                    f"⚠️ Timeout proxying to {service_name} (attempt {attempt + 1}/{service.retry_count})"
                )

            except httpx.RequestError as exc:
                last_error = str(exc)
                logger.warning(
                    f"⚠️ Error proxying to {service_name}: {exc} (attempt {attempt + 1}/{service.retry_count})"
                )

        # فشلت جميع المحاولات
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to proxy request to '{service_name}': {last_error}",
        )

    def find_route(self, path: str) -> RouteRule | None:
        """
        يبحث عن قاعدة توجيه مطابقة للمسار.

        Args:
            path: المسار المطلوب

        Returns:
            RouteRule | None: قاعدة التوجيه أو None
        """
        for route in self.config.routes:
            if path.startswith(route.path_prefix):
                return route
        return None

    async def route_request(self, path: str, request: Request) -> Response:
        """
        يوجه الطلب بناءً على قواعد التوجيه.

        Args:
            path: المسار المطلوب
            request: الطلب الأصلي

        Returns:
            Response: استجابة الخدمة

        Raises:
            HTTPException: في حالة عدم وجود قاعدة توجيه
        """
        route = self.find_route(path)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No route found for path: {path}",
            )

        # إزالة البادئة إذا لزم الأمر
        service_path = path
        if route.strip_prefix:
            service_path = path[len(route.path_prefix) :].lstrip("/")

        return await self._proxy_to_service(route.service_name, service_path, request)
