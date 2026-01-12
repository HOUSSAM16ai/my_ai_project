"""
نظام اكتشاف الخدمات (Service Discovery).

يوفر آلية ديناميكية لتسجيل واكتشاف الخدمات المصغرة.
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.gateway.config import ServiceEndpoint
from app.gateway.registry import ServiceHealth, ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceInstance:
    """
    مثيل خدمة مسجل.

    Attributes:
        endpoint: معلومات نقطة النهاية
        registered_at: وقت التسجيل
        last_heartbeat: آخر نبضة قلب
        metadata: بيانات وصفية إضافية
    """

    endpoint: ServiceEndpoint
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


type HealthCheckCallback = Callable[[str, ServiceHealth], None]


class ServiceDiscovery:
    """
    نظام اكتشاف الخدمات الديناميكي.

    الميزات:
    - تسجيل ديناميكي للخدمات
    - فحص صحة دوري
    - إزالة الخدمات غير المستجيبة
    - إشعارات التغييرات
    - موازنة الحمل

    المبادئ:
    - Self-Healing: إزالة الخدمات الميتة تلقائياً
    - Dynamic: دعم إضافة/إزالة الخدمات في وقت التشغيل
    - Observable: إشعارات عن تغييرات الحالة
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        health_check_interval: int = 30,
        heartbeat_timeout: int = 90,
    ) -> None:
        """
        تهيئة نظام الاكتشاف.

        Args:
            registry: سجل الخدمات
            health_check_interval: فترة فحص الصحة بالثواني
            heartbeat_timeout: مهلة نبضة القلب بالثواني
        """
        self.registry = registry
        self.health_check_interval = health_check_interval
        self.heartbeat_timeout = heartbeat_timeout

        self._instances: dict[str, list[ServiceInstance]] = {}
        self._health_callbacks: list[HealthCheckCallback] = []
        self._running = False
        self._health_check_task: asyncio.Task[None] | None = None

        logger.info("✅ Service Discovery initialized")

    def register_service(
        self,
        endpoint: ServiceEndpoint,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceInstance:
        """
        يسجل خدمة جديدة.

        Args:
            endpoint: معلومات نقطة النهاية
            metadata: بيانات وصفية إضافية

        Returns:
            ServiceInstance: مثيل الخدمة المسجل
        """
        instance = ServiceInstance(
            endpoint=endpoint,
            metadata=metadata or {},
        )

        if endpoint.name not in self._instances:
            self._instances[endpoint.name] = []

        self._instances[endpoint.name].append(instance)

        logger.info(f"✅ Service registered: {endpoint.name} at {endpoint.base_url}")

        return instance

    def deregister_service(self, name: str, base_url: str) -> bool:
        """
        يلغي تسجيل خدمة.

        Args:
            name: اسم الخدمة
            base_url: عنوان URL

        Returns:
            bool: True إذا تم الإلغاء بنجاح
        """
        if name not in self._instances:
            return False

        instances = self._instances[name]
        original_count = len(instances)

        self._instances[name] = [inst for inst in instances if inst.endpoint.base_url != base_url]

        removed = original_count - len(self._instances[name])

        if removed > 0:
            logger.info(f"✅ Service deregistered: {name} at {base_url}")
            return True

        return False

    def get_instances(self, name: str) -> list[ServiceInstance]:
        """
        يحصل على جميع مثيلات خدمة.

        Args:
            name: اسم الخدمة

        Returns:
            list[ServiceInstance]: قائمة المثيلات
        """
        return self._instances.get(name, [])

    def get_healthy_instance(self, name: str) -> ServiceInstance | None:
        """
        يحصل على مثيل صحي للخدمة (موازنة حمل بسيطة).

        Args:
            name: اسم الخدمة

        Returns:
            ServiceInstance | None: مثيل صحي أو None
        """
        instances = self.get_instances(name)
        if not instances:
            return None

        # فلترة المثيلات الصحية
        healthy_instances = [inst for inst in instances if self._is_instance_healthy(inst)]

        if not healthy_instances:
            return None

        # موازنة حمل بسيطة: Round Robin
        # في الإنتاج، يمكن استخدام خوارزميات أكثر تعقيداً
        return healthy_instances[0]

    def _is_instance_healthy(self, instance: ServiceInstance) -> bool:
        """
        يتحقق من صحة مثيل.

        Args:
            instance: مثيل الخدمة

        Returns:
            bool: True إذا كان صحياً
        """
        # التحقق من نبضة القلب
        time_since_heartbeat = datetime.utcnow() - instance.last_heartbeat
        if time_since_heartbeat > timedelta(seconds=self.heartbeat_timeout):
            return False

        # التحقق من حالة الصحة في السجل
        health = self.registry.get_health(instance.endpoint.name)
        return not (health and not health.is_healthy)

    def heartbeat(self, name: str, base_url: str) -> bool:
        """
        يسجل نبضة قلب لخدمة.

        Args:
            name: اسم الخدمة
            base_url: عنوان URL

        Returns:
            bool: True إذا تم التسجيل بنجاح
        """
        instances = self.get_instances(name)

        for instance in instances:
            if instance.endpoint.base_url == base_url:
                instance.last_heartbeat = datetime.utcnow()
                logger.debug(f"💓 Heartbeat received: {name} at {base_url}")
                return True

        return False

    def add_health_callback(self, callback: HealthCheckCallback) -> None:
        """
        يضيف callback لإشعارات الصحة.

        Args:
            callback: دالة الإشعار
        """
        self._health_callbacks.append(callback)

    async def start_health_checks(self) -> None:
        """يبدأ فحوصات الصحة الدورية."""
        if self._running:
            logger.warning("⚠️ Health checks already running")
            return

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("✅ Health checks started")

    async def stop_health_checks(self) -> None:
        """يوقف فحوصات الصحة."""
        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task

        logger.info("🛑 Health checks stopped")

    async def _health_check_loop(self) -> None:
        """حلقة فحص الصحة الدورية."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"❌ Error in health check loop: {exc}", exc_info=True)
                await asyncio.sleep(self.health_check_interval)

    async def _perform_health_checks(self) -> None:
        """ينفذ فحوصات الصحة لجميع الخدمات."""
        for name, instances in self._instances.items():
            for _instance in instances:
                try:
                    health = await self.registry.check_health(name)

                    # إشعار الـ callbacks
                    for callback in self._health_callbacks:
                        try:
                            callback(name, health)
                        except Exception as exc:
                            logger.error(
                                f"❌ Error in health callback: {exc}",
                                exc_info=True,
                            )

                    # إزالة المثيلات غير الصحية
                    if not health.is_healthy:
                        self._remove_unhealthy_instances(name)

                except Exception as exc:
                    logger.error(
                        f"❌ Error checking health for {name}: {exc}",
                        exc_info=True,
                    )

    def _remove_unhealthy_instances(self, name: str) -> None:
        """
        يزيل المثيلات غير الصحية.

        Args:
            name: اسم الخدمة
        """
        if name not in self._instances:
            return

        original_count = len(self._instances[name])

        self._instances[name] = [
            inst for inst in self._instances[name] if self._is_instance_healthy(inst)
        ]

        removed = original_count - len(self._instances[name])

        if removed > 0:
            logger.warning(f"⚠️ Removed {removed} unhealthy instances of {name}")

    def get_service_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات الخدمات.

        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        stats = {
            "total_services": len(self._instances),
            "total_instances": sum(len(insts) for insts in self._instances.values()),
            "services": {},
        }

        for name, instances in self._instances.items():
            healthy_count = sum(1 for inst in instances if self._is_instance_healthy(inst))

            stats["services"][name] = {
                "total_instances": len(instances),
                "healthy_instances": healthy_count,
                "unhealthy_instances": len(instances) - healthy_count,
            }

        return stats
