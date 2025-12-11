# app/services/adaptive/facade.py
"""
Self-Adaptive Microservices Facade
===================================
Backward-compatible facade maintaining original API.
"""

from __future__ import annotations

import statistics
import threading
from collections import defaultdict
from datetime import datetime
from typing import Any

from app.services.adaptive.domain.models import (
    ScalingDecision,
    ScalingDirection,
    ServiceHealth,
    ServiceInstance,
    ServiceMetrics,
)
from app.services.adaptive.application.scaling_engine import AIScalingEngine
from app.services.adaptive.application.intelligent_router import IntelligentRouter
from app.services.adaptive.application.health_monitor import PredictiveHealthMonitor


class SelfAdaptiveMicroservices:
    """
    النظام الرئيسي للخدمات المصغرة ذاتية التكيف
    
    Maintains backward compatibility with original monolithic API
    while delegating to clean hexagonal architecture.
    """

    def __init__(self):
        self.services: dict[str, list[ServiceInstance]] = defaultdict(list)
        self.scaling_engine = AIScalingEngine()
        self.router = IntelligentRouter()
        self.health_monitor = PredictiveHealthMonitor()
        self.lock = threading.RLock()  # Use RLock to prevent deadlock with nested calls

    def register_service(
        self, service_name: str, initial_instances: int = 1
    ) -> list[ServiceInstance]:
        """
        تسجيل خدمة جديدة مع المثيلات الأولية
        """
        with self.lock:
            instances = []
            for i in range(initial_instances):
                instance = ServiceInstance(
                    instance_id=f"{service_name}-{i}",
                    service_name=service_name,
                    status=ServiceHealth.HEALTHY,
                )
                instances.append(instance)

            self.services[service_name] = instances
            return instances

    def update_metrics(self, service_name: str, instance_id: str, metrics: ServiceMetrics):
        """
        تحديث مقاييس instance محدد
        """
        with self.lock:
            for instance in self.services[service_name]:
                if instance.instance_id == instance_id:
                    instance.metrics_history.append(metrics)

                    # Update health status
                    health, warnings = self.health_monitor.analyze_health(service_name, metrics)
                    instance.status = health
                    instance.last_health_check = datetime.now()

                    if warnings:
                        print(f"⚠️ Health warnings for {instance_id}:")
                        for warning in warnings:
                            print(f"  - {warning}")

                    break

    def auto_scale(self, service_name: str) -> ScalingDecision | None:
        """
        التوسع التلقائي بناءً على AI analysis
        """
        with self.lock:
            instances = self.services.get(service_name, [])
            if not instances:
                return None

            # Get latest metrics
            healthy_instances = [i for i in instances if i.metrics_history]
            if not healthy_instances:
                return None

            # Use metrics from most loaded instance
            all_metrics = [i.metrics_history[-1] for i in healthy_instances]
            avg_metrics = self._aggregate_metrics(service_name, all_metrics)

            # Calculate scaling decision
            decision = self.scaling_engine.calculate_optimal_instances(
                service_name, avg_metrics, len(instances)
            )

            # Execute scaling
            if decision.direction == ScalingDirection.UP:
                self._scale_up(service_name, decision.target_instances - len(instances))
            elif decision.direction == ScalingDirection.DOWN:
                self._scale_down(service_name, len(instances) - decision.target_instances)

            return decision

    def _aggregate_metrics(
        self, service_name: str, metrics_list: list[ServiceMetrics]
    ) -> ServiceMetrics:
        """
        دمج مقاييس من instances متعددة
        """
        if not metrics_list:
            return ServiceMetrics(
                service_name=service_name,
                timestamp=datetime.now(),
                cpu_usage=0,
                memory_usage=0,
                request_rate=0,
                error_rate=0,
                latency_p50=0,
                latency_p95=0,
                latency_p99=0,
                active_connections=0,
                queue_depth=0,
            )

        return ServiceMetrics(
            service_name=service_name,
            timestamp=datetime.now(),
            cpu_usage=statistics.mean([m.cpu_usage for m in metrics_list]),
            memory_usage=statistics.mean([m.memory_usage for m in metrics_list]),
            request_rate=sum([m.request_rate for m in metrics_list]),
            error_rate=statistics.mean([m.error_rate for m in metrics_list]),
            latency_p50=statistics.median([m.latency_p50 for m in metrics_list]),
            latency_p95=statistics.median([m.latency_p95 for m in metrics_list]),
            latency_p99=max([m.latency_p99 for m in metrics_list]),
            active_connections=sum([m.active_connections for m in metrics_list]),
            queue_depth=sum([m.queue_depth for m in metrics_list]),
        )

    def _scale_up(self, service_name: str, count: int):
        """إضافة instances جديدة"""
        current_count = len(self.services[service_name])
        for i in range(count):
            instance = ServiceInstance(
                instance_id=f"{service_name}-{current_count + i}",
                service_name=service_name,
                status=ServiceHealth.HEALTHY,
            )
            self.services[service_name].append(instance)
        print(f"✅ Scaled UP {service_name}: +{count} instances")

    def _scale_down(self, service_name: str, count: int):
        """إزالة instances"""
        if count >= len(self.services[service_name]):
            count = len(self.services[service_name]) - 1  # Keep at least 1

        # Remove least loaded instances
        instances = self.services[service_name]
        instances.sort(
            key=lambda i: i.metrics_history[-1].active_connections if i.metrics_history else 0
        )

        for _ in range(count):
            if len(instances) > 1:
                removed = instances.pop(0)
                print(f"✅ Scaled DOWN {service_name}: removed {removed.instance_id}")

    def route_request(
        self, service_name: str, request_metadata: dict | None = None
    ) -> ServiceInstance | None:
        """
        توجيه طلب إلى أفضل instance
        """
        instances = self.services.get(service_name, [])
        return self.router.select_instance(service_name, instances, request_metadata)

    def get_service_status(self, service_name: str) -> dict[str, Any]:
        """
        الحصول على حالة الخدمة الكاملة
        """
        with self.lock:
            instances = self.services.get(service_name, [])

            if not instances:
                return {"service_name": service_name, "status": "not_found", "instances": 0}

            # Calculate aggregate metrics
            healthy_count = sum(1 for i in instances if i.status == ServiceHealth.HEALTHY)

            # Predict failure
            latest_metrics = []
            for inst in instances:
                if inst.metrics_history:
                    latest_metrics.append(inst.metrics_history[-1])

            failure_prob = 0.0
            risk_factors = []
            if latest_metrics:
                self._aggregate_metrics(service_name, latest_metrics)
                failure_prob, risk_factors = self.health_monitor.predict_failure(service_name)

            return {
                "service_name": service_name,
                "total_instances": len(instances),
                "healthy_instances": healthy_count,
                "overall_health": "healthy" if healthy_count / len(instances) > 0.7 else "degraded",
                "failure_probability": failure_prob,
                "risk_factors": risk_factors,
                "instances": [
                    {
                        "id": i.instance_id,
                        "status": i.status.value,
                        "uptime": (datetime.now() - i.created_at).total_seconds(),
                    }
                    for i in instances
                ],
            }


# Singleton instance for backward compatibility
_instance: SelfAdaptiveMicroservices | None = None
_lock = threading.Lock()


def get_adaptive_microservices() -> SelfAdaptiveMicroservices:
    """Get or create singleton instance"""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = SelfAdaptiveMicroservices()
    return _instance
