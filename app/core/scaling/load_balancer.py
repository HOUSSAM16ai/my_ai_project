"""
Load balancer for distributing requests across instances.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import TypeVar

from app.core.scaling.service_registry import ServiceInstance, ServiceRegistry

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LoadBalancingStrategy(ABC):
    """Base load balancing strategy."""

    @abstractmethod
    async def select(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select instance using strategy."""
        pass


class RoundRobinStrategy(LoadBalancingStrategy):
    """Round-robin load balancing."""

    def __init__(self):
        self._counter = 0
        self._lock = asyncio.Lock()

    async def select(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select next instance in round-robin fashion."""
        if not instances:
            return None
        
        async with self._lock:
            instance = instances[self._counter % len(instances)]
            self._counter += 1
            return instance


class RandomStrategy(LoadBalancingStrategy):
    """Random load balancing."""

    async def select(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select random instance."""
        if not instances:
            return None
        return random.choice(instances)


class WeightedRandomStrategy(LoadBalancingStrategy):
    """Weighted random load balancing."""

    async def select(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select instance based on weights."""
        if not instances:
            return None
        
        total_weight = sum(i.weight for i in instances)
        if total_weight == 0:
            return random.choice(instances)
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for instance in instances:
            cumulative += instance.weight
            if r <= cumulative:
                return instance
        
        return instances[-1]


class LeastConnectionsStrategy(LoadBalancingStrategy):
    """Least connections load balancing."""

    def __init__(self):
        self._connections: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def select(self, instances: list[ServiceInstance]) -> ServiceInstance | None:
        """Select instance with least connections."""
        if not instances:
            return None
        
        async with self._lock:
            # Find instance with minimum connections
            min_conn = float('inf')
            selected = instances[0]
            
            for instance in instances:
                conn = self._connections.get(instance.id, 0)
                if conn < min_conn:
                    min_conn = conn
                    selected = instance
            
            # Increment connection count
            self._connections[selected.id] = self._connections.get(selected.id, 0) + 1
            
            return selected

    async def release(self, instance_id: str) -> None:
        """Release connection."""
        async with self._lock:
            if instance_id in self._connections:
                self._connections[instance_id] = max(0, self._connections[instance_id] - 1)


class LoadBalancer:
    """
    Load balancer for distributing requests.
    
    Critical component for horizontal scaling.
    """

    def __init__(
        self,
        service_registry: ServiceRegistry,
        strategy: LoadBalancingStrategy | None = None,
    ):
        self.registry = service_registry
        self.strategy = strategy or RoundRobinStrategy()

    async def get_instance(self, service_name: str) -> ServiceInstance | None:
        """
        Get instance for service using load balancing strategy.
        
        Complexity: 2
        """
        instances = await self.registry.get_instances(service_name, healthy_only=True)
        
        if not instances:
            logger.warning(f"No healthy instances available for {service_name}")
            return None
        
        return await self.strategy.select(instances)

    async def execute_on_instance(
        self,
        service_name: str,
        func,
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function on selected instance.
        
        Complexity: 2
        """
        instance = await self.get_instance(service_name)
        
        if not instance:
            raise RuntimeError(f"No instances available for {service_name}")
        
        try:
            return await func(instance, *args, **kwargs)
        finally:
            # Release connection if using least connections
            if isinstance(self.strategy, LeastConnectionsStrategy):
                await self.strategy.release(instance.id)
