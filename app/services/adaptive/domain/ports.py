# app/services/adaptive/domain/ports.py
"""
Adaptive Microservices Domain Ports
====================================
Interface definitions for repositories and external services.
"""

from __future__ import annotations

from typing import Protocol

from app.services.adaptive.domain.models import ServiceInstance, ServiceMetrics


class ServiceInstanceRepository(Protocol):
    """Repository for service instance management"""

    def create(self, instance: ServiceInstance) -> str:
        """Create new service instance"""
        ...

    def get(self, instance_id: str) -> ServiceInstance | None:
        """Get service instance by ID"""
        ...

    def update(self, instance: ServiceInstance) -> None:
        """Update service instance"""
        ...

    def delete(self, instance_id: str) -> None:
        """Delete service instance"""
        ...

    def list_by_service(self, service_name: str) -> list[ServiceInstance]:
        """List all instances for a service"""
        ...

class MetricsRepository(Protocol):
    """Repository for metrics storage and retrieval"""

    def store_metrics(self, metrics: ServiceMetrics) -> None:
        """Store service metrics"""
        ...

    def get_recent_metrics(
        self, service_name: str, count: int = 100
    ) -> list[ServiceMetrics]:
        """Get recent metrics for a service"""
        ...

    def get_metrics_in_range(
        self, service_name: str, start_time: float, end_time: float
    ) -> list[ServiceMetrics]:
        """Get metrics within a time range"""
        ...
