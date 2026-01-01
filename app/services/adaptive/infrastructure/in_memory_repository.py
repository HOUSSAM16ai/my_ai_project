# app/services/adaptive/infrastructure/in_memory_repository.py
"""
In-Memory Repository Implementation
====================================
In-memory storage for service instances and metrics.
"""

from __future__ import annotations

from collections import defaultdict

from app.services.adaptive.domain.models import ServiceInstance, ServiceMetrics

class InMemoryServiceInstanceRepository:
    """In-memory repository for service instances"""

    def __init__(self):
        self._instances: dict[str, ServiceInstance] = {}
        self._services: dict[str, list[str]] = defaultdict(list)

    def create(self, instance: ServiceInstance) -> str:
        """Create new service instance"""
        self._instances[instance.instance_id] = instance
        if instance.instance_id not in self._services[instance.service_name]:
            self._services[instance.service_name].append(instance.instance_id)
        return instance.instance_id

    def get(self, instance_id: str) -> ServiceInstance | None:
        """Get service instance by ID"""
        return self._instances.get(instance_id)

    def update(self, instance: ServiceInstance) -> None:
        """Update service instance"""
        if instance.instance_id in self._instances:
            self._instances[instance.instance_id] = instance

    def delete(self, instance_id: str) -> None:
        """Delete service instance"""
        if instance_id in self._instances:
            instance = self._instances[instance_id]
            # Remove from service list
            if instance_id in self._services[instance.service_name]:
                self._services[instance.service_name].remove(instance_id)
            # Remove instance
            del self._instances[instance_id]

    def list_by_service(self, service_name: str) -> list[ServiceInstance]:
        """List all instances for a service"""
        instance_ids = self._services.get(service_name, [])
        return [self._instances[iid] for iid in instance_ids if iid in self._instances]

class InMemoryMetricsRepository:
    """In-memory repository for metrics"""

    def __init__(self):
        self._metrics: dict[str, list[ServiceMetrics]] = defaultdict(list)

    def store_metrics(self, metrics: ServiceMetrics) -> None:
        """Store service metrics"""
        self._metrics[metrics.service_name].append(metrics)
        # Keep only recent metrics (last 1000)
        if len(self._metrics[metrics.service_name]) > 1000:
            self._metrics[metrics.service_name] = self._metrics[metrics.service_name][-1000:]

    def get_recent_metrics(
        self, service_name: str, count: int = 100
    ) -> list[ServiceMetrics]:
        """Get recent metrics for a service"""
        metrics_list = self._metrics.get(service_name, [])
        return metrics_list[-count:] if metrics_list else []

    def get_metrics_in_range(
        self, service_name: str, start_time: float, end_time: float
    ) -> list[ServiceMetrics]:
        """Get metrics within a time range"""
        all_metrics = self._metrics.get(service_name, [])
        return [
            m
            for m in all_metrics
            if start_time <= m.timestamp.timestamp() <= end_time
        ]
