"""
Health checker for monitoring service instances.
"""

import asyncio
import logging
from typing import Callable

from app.core.scaling.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Health checker for monitoring service instances.
    
    Continuously monitors instance health for load balancing.
    """

    def __init__(
        self,
        service_registry: ServiceRegistry,
        check_interval: float = 10.0,
    ):
        self.registry = service_registry
        self.check_interval = check_interval
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start health checking."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Health checker started")

    async def stop(self) -> None:
        """Stop health checking."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")

    async def _check_loop(self) -> None:
        """Main health check loop."""
        while self._running:
            try:
                await self._check_all_services()
                await self.registry.cleanup_stale_instances()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_services(self) -> None:
        """Check health of all registered services."""
        stats = self.registry.get_stats()
        
        for service_name in stats.keys():
            instances = await self.registry.get_instances(
                service_name,
                healthy_only=False
            )
            
            for instance in instances:
                healthy = await self._check_instance_health(instance)
                await self.registry.update_health(
                    service_name,
                    instance.id,
                    healthy
                )

    async def _check_instance_health(self, instance) -> bool:
        """
        Check if instance is healthy.
        
        Override this method to implement custom health checks.
        """
        # Default: assume healthy if recently heartbeat
        return instance.healthy

    def register_health_check(
        self,
        service_name: str,
        check_func: Callable,
    ) -> None:
        """Register custom health check function."""
        # Placeholder for custom health checks
        pass
