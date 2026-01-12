"""
سجل الخدمات (Service Registry).

يدير تسجيل واكتشاف الخدمات المصغرة بشكل ديناميكي.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

import httpx

from app.gateway.config import ServiceEndpoint

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceHealth:
    """
    حالة صحة الخدمة.

    Attributes:
        is_healthy: هل الخدمة صحية
        last_check: آخر فحص
        response_time_ms: وقت الاستجابة بالميلي ثانية
        error_message: رسالة الخطأ إن وجدت
    """

    is_healthy: bool
    last_check: datetime
    response_time_ms: float | None = None
    error_message: str | None = None


class ServiceRegistry:
    """
    سجل الخدمات المصغرة.

    يوفر:
    - تسجيل الخدمات
    - اكتشاف الخدمات
    - فحص الصحة
    - موازنة الحمل (Load Balancing) البسيطة

    المبادئ:
    - Functional Core: البيانات منفصلة عن المنطق
    - Immutability: الخدمات المسجلة ثابتة
    - Explicit State: الحالة واضحة ومحددة
    """

    def __init__(
        self,
        services: tuple[ServiceEndpoint, ...] = (),
        health_check_interval: int = 30,
    ) -> None:
        """
        تهيئة السجل.

        Args:
            services: قائمة الخدمات المسجلة
            health_check_interval: فترة فحص الصحة بالثواني
        """
        self._services: Final[dict[str, ServiceEndpoint]] = {svc.name: svc for svc in services}
        self._health: dict[str, ServiceHealth] = {}
        self._health_check_interval = health_check_interval

        logger.info(f"✅ Service Registry initialized with {len(self._services)} services")

    def get_service(self, name: str) -> ServiceEndpoint | None:
        """
        يحصل على معلومات خدمة بالاسم.

        Args:
            name: اسم الخدمة

        Returns:
            ServiceEndpoint | None: معلومات الخدمة أو None
        """
        return self._services.get(name)

    def list_services(self) -> Mapping[str, ServiceEndpoint]:
        """
        يعرض جميع الخدمات المسجلة.

        Returns:
            Mapping[str, ServiceEndpoint]: قاموس الخدمات
        """
        return self._services

    def get_health(self, name: str) -> ServiceHealth | None:
        """
        يحصل على حالة صحة خدمة.

        Args:
            name: اسم الخدمة

        Returns:
            ServiceHealth | None: حالة الصحة أو None
        """
        return self._health.get(name)

    async def check_health(self, name: str) -> ServiceHealth:
        """
        يفحص صحة خدمة معينة.

        Args:
            name: اسم الخدمة

        Returns:
            ServiceHealth: حالة الصحة
        """
        service = self.get_service(name)
        if not service:
            return ServiceHealth(
                is_healthy=False,
                last_check=datetime.utcnow(),
                error_message=f"Service '{name}' not found in registry",
            )

        health_url = f"{service.base_url}{service.health_path}"
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response.raise_for_status()

                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000

                health = ServiceHealth(
                    is_healthy=True,
                    last_check=end_time,
                    response_time_ms=response_time,
                )

                self._health[name] = health
                logger.debug(f"✅ Service '{name}' is healthy ({response_time:.2f}ms)")
                return health

        except Exception as exc:
            end_time = datetime.utcnow()
            health = ServiceHealth(
                is_healthy=False,
                last_check=end_time,
                error_message=str(exc),
            )

            self._health[name] = health
            logger.warning(f"❌ Service '{name}' health check failed: {exc}")
            return health

    async def check_all_health(self) -> dict[str, ServiceHealth]:
        """
        يفحص صحة جميع الخدمات.

        Returns:
            dict[str, ServiceHealth]: حالة صحة جميع الخدمات
        """
        results = {}
        for name in self._services:
            results[name] = await self.check_health(name)
        return results

    def should_check_health(self, name: str) -> bool:
        """
        يحدد ما إذا كان يجب فحص صحة الخدمة.

        Args:
            name: اسم الخدمة

        Returns:
            bool: True إذا كان يجب الفحص
        """
        health = self._health.get(name)
        if not health:
            return True

        time_since_check = datetime.utcnow() - health.last_check
        return time_since_check > timedelta(seconds=self._health_check_interval)

    def get_healthy_services(self) -> list[str]:
        """
        يعرض قائمة الخدمات الصحية.

        Returns:
            list[str]: أسماء الخدمات الصحية
        """
        return [name for name, health in self._health.items() if health.is_healthy]
