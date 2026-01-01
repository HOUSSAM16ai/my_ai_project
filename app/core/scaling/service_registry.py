"""
Service registry for service discovery.
"""
from typing import Any

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ServiceInstance:
    """Service instance metadata."""
    id: str
    host: str
    port: int
    metadata: dict[str, Any] = field(default_factory=dict)
    healthy: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    weight: int = 1

    @property
    def address(self) ->str:
        """Get service address."""
        return f'{self.host}:{self.port}'

class ServiceRegistry:
    """
    Service registry for dynamic service discovery.

    Enables horizontal scaling by tracking available instances.
    """

    def __init__(self, heartbeat_timeout: float=30.0):
        self._services: dict[str, dict[str, ServiceInstance]] = {}
        self._lock = asyncio.Lock()
        self.heartbeat_timeout = heartbeat_timeout

    async def register(self, service_name: str, instance: ServiceInstance
        ) ->None:
        """Register service instance."""
        async with self._lock:
            if service_name not in self._services:
                self._services[service_name] = {}
            self._services[service_name][instance.id] = instance
            logger.info(
                f'Service registered: {service_name}/{instance.id} at {instance.address}'
                )

    async def get_instances(self, service_name: str, healthy_only: bool=True
        ) ->list[ServiceInstance]:
        """Get all instances of a service."""
        async with self._lock:
            if service_name not in self._services:
                return []
            instances = list(self._services[service_name].values())
            if healthy_only:
                instances = [i for i in instances if i.healthy]
            return instances

    async def update_health(self, service_name: str, instance_id: str,
        healthy: bool) ->None:
        """Update instance health status."""
        async with self._lock:
            if (service_name in self._services and instance_id in self.
                _services[service_name]):
                instance = self._services[service_name][instance_id]
                instance.healthy = healthy
                instance.last_heartbeat = datetime.now()

    async def cleanup_stale_instances(self) ->None:
        """Remove instances that haven't sent heartbeat."""
        async with self._lock:
            now = datetime.now()
            for service_name, instances in list(self._services.items()):
                for instance_id, instance in list(instances.items()):
                    age = (now - instance.last_heartbeat).total_seconds()
                    if age > self.heartbeat_timeout:
                        del instances[instance_id]
                        logger.warning(
                            f'Removed stale instance: {service_name}/{instance_id}'
                            )

    def get_stats(self) ->dict[str, Any]:
        """Get registry statistics."""
        stats = {}
        for service_name, instances in self._services.items():
            healthy = sum(1 for i in instances.values() if i.healthy)
            stats[service_name] = {'total': len(instances), 'healthy':
                healthy, 'unhealthy': len(instances) - healthy}
        return stats
