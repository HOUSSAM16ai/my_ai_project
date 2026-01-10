"""
اختبارات بوابة API (API Gateway Tests).

يختبر هذا الملف جميع وظائف البوابة بما في ذلك:
- التوجيه
- سجل الخدمات
- فحص الصحة
- إعادة المحاولة
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.gateway import APIGateway, GatewayConfig, ServiceRegistry
from app.gateway.config import RouteRule, ServiceEndpoint
from app.gateway.registry import ServiceHealth


class TestServiceRegistry:
    """اختبارات سجل الخدمات."""

    def test_registry_initialization(self) -> None:
        """يختبر تهيئة السجل."""
        services = (
            ServiceEndpoint(name="test-service", base_url="http://localhost:8001"),
        )
        registry = ServiceRegistry(services=services)

        assert len(registry.list_services()) == 1
        assert registry.get_service("test-service") is not None
        assert registry.get_service("unknown") is None

    def test_get_service(self) -> None:
        """يختبر الحصول على خدمة."""
        service = ServiceEndpoint(name="test-service", base_url="http://localhost:8001")
        registry = ServiceRegistry(services=(service,))

        retrieved = registry.get_service("test-service")
        assert retrieved is not None
        assert retrieved.name == "test-service"
        assert retrieved.base_url == "http://localhost:8001"

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        """يختبر فحص الصحة الناجح."""
        service = ServiceEndpoint(
            name="test-service",
            base_url="http://localhost:8001",
            health_path="/health",
        )
        registry = ServiceRegistry(services=(service,))

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            health = await registry.check_health("test-service")

            assert health.is_healthy is True
            assert health.response_time_ms is not None
            assert health.error_message is None

    @pytest.mark.asyncio
    async def test_health_check_failure(self) -> None:
        """يختبر فحص الصحة الفاشل."""
        service = ServiceEndpoint(
            name="test-service",
            base_url="http://localhost:8001",
        )
        registry = ServiceRegistry(services=(service,))

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            health = await registry.check_health("test-service")

            assert health.is_healthy is False
            assert health.error_message is not None

    def test_get_healthy_services(self) -> None:
        """يختبر الحصول على الخدمات الصحية."""
        services = (
            ServiceEndpoint(name="service1", base_url="http://localhost:8001"),
            ServiceEndpoint(name="service2", base_url="http://localhost:8002"),
        )
        registry = ServiceRegistry(services=services)

        # إضافة حالات صحة يدوياً
        from datetime import datetime
        registry._health["service1"] = ServiceHealth(
            is_healthy=True,
            last_check=datetime.utcnow(),
        )
        registry._health["service2"] = ServiceHealth(
            is_healthy=False,
            last_check=datetime.utcnow(),
        )

        healthy = registry.get_healthy_services()
        assert len(healthy) == 1
        assert "service1" in healthy


class TestAPIGateway:
    """اختبارات بوابة API."""

    def test_gateway_initialization(self) -> None:
        """يختبر تهيئة البوابة."""
        config = GatewayConfig(
            services=(
                ServiceEndpoint(name="test-service", base_url="http://localhost:8001"),
            ),
            routes=(
                RouteRule(path_prefix="/api/test", service_name="test-service"),
            ),
        )

        gateway = APIGateway(config=config)

        assert gateway.config == config
        assert gateway.registry is not None
        assert gateway.router is not None

    def test_find_route(self) -> None:
        """يختبر البحث عن قاعدة توجيه."""
        config = GatewayConfig(
            routes=(
                RouteRule(path_prefix="/api/v1/users", service_name="user-service"),
                RouteRule(path_prefix="/api/v1/plans", service_name="planning-agent"),
            ),
        )

        gateway = APIGateway(config=config)

        route = gateway.find_route("/api/v1/users/123")
        assert route is not None
        assert route.service_name == "user-service"

        route = gateway.find_route("/api/v1/plans")
        assert route is not None
        assert route.service_name == "planning-agent"

        route = gateway.find_route("/api/v1/unknown")
        assert route is None


class TestGatewayConfig:
    """اختبارات تكوين البوابة."""

    def test_service_endpoint_creation(self) -> None:
        """يختبر إنشاء نقطة نهاية خدمة."""
        endpoint = ServiceEndpoint(
            name="test-service",
            base_url="http://localhost:8001",
            health_path="/health",
            timeout=30,
            retry_count=3,
        )

        assert endpoint.name == "test-service"
        assert endpoint.base_url == "http://localhost:8001"
        assert endpoint.health_path == "/health"
        assert endpoint.timeout == 30
        assert endpoint.retry_count == 3

    def test_route_rule_creation(self) -> None:
        """يختبر إنشاء قاعدة توجيه."""
        rule = RouteRule(
            path_prefix="/api/v1/test",
            service_name="test-service",
            strip_prefix=True,
            require_auth=True,
        )

        assert rule.path_prefix == "/api/v1/test"
        assert rule.service_name == "test-service"
        assert rule.strip_prefix is True
        assert rule.require_auth is True

    def test_gateway_config_immutability(self) -> None:
        """يختبر ثبات التكوين."""
        config = GatewayConfig(
            services=(
                ServiceEndpoint(name="test", base_url="http://localhost:8001"),
            ),
        )

        # يجب أن يكون التكوين ثابتاً (frozen)
        with pytest.raises(AttributeError):
            config.services = ()  # type: ignore
