# app/services/adaptive/application/intelligent_router.py
"""
Intelligent Router
==================
موجه ذكي يستخدم ML لاختيار أفضل instance للطلب.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.services.adaptive.domain.models import ServiceHealth, ServiceInstance


class IntelligentRouter:
    """
    موجه ذكي يستخدم ML لاختيار أفضل instance للطلب
    """

    def __init__(self):
        self.routing_history = defaultdict(list)
        self.instance_scores = defaultdict(float)

    def select_instance(
        self,
        service_name: str,
        instances: list[ServiceInstance],
        request_metadata: dict | None = None,
    ) -> ServiceInstance | None:
        """
        اختيار أفضل instance بناءً على ML scoring
        Select best instance using ML scoring

        Args:
            service_name: اسم الخدمة | Service name
            instances: قائمة instances المتاحة | Available instances
            request_metadata: بيانات الطلب | Request metadata

        Returns:
            أفضل instance أو None | Best instance or None
        """
        if not instances:
            return None

        # Filter and select healthy instances
        selected_instance = self._select_healthy_instance(instances)
        if not selected_instance:
            return None

        # Record routing decision
        self._record_routing_decision(service_name, selected_instance, request_metadata)

        return selected_instance

    def _select_healthy_instance(
        self, instances: list[ServiceInstance]
    ) -> ServiceInstance | None:
        """
        تصفية واختيار instance صحي | Filter and select healthy instance

        Args:
            instances: قائمة instances | Instances list

        Returns:
            أفضل instance صحي | Best healthy instance
        """
        # Filter healthy instances
        healthy_instances = [i for i in instances if i.is_healthy()]

        if not healthy_instances:
            # Fallback to degraded instances
            return self._select_degraded_instance(instances)

        # Score and select best
        return self._select_best_scored_instance(healthy_instances)

    def _select_degraded_instance(
        self, instances: list[ServiceInstance]
    ) -> ServiceInstance | None:
        """
        اختيار instance متدهور كحل بديل | Select degraded instance as fallback

        Args:
            instances: قائمة instances | Instances list

        Returns:
            أول instance متدهور أو None | First degraded instance or None
        """
        degraded = [i for i in instances if i.status == ServiceHealth.DEGRADED]
        return degraded[0] if degraded else None

    def _select_best_scored_instance(
        self, instances: list[ServiceInstance]
    ) -> ServiceInstance:
        """
        تسجيل واختيار أفضل instance | Score and select best instance

        Args:
            instances: قائمة instances الصحية | Healthy instances list

        Returns:
            أفضل instance بناءً على النقاط | Best scored instance
        """
        # Score each instance
        scored_instances = [
            (self._calculate_instance_score(instance, None), instance)
            for instance in instances
        ]

        # Sort by score (higher is better) and return best
        scored_instances.sort(reverse=True, key=lambda x: x[0])
        return scored_instances[0][1]

    def _record_routing_decision(
        self,
        service_name: str,
        instance: ServiceInstance,
        request_metadata: dict | None,
    ) -> None:
        """
        تسجيل قرار التوجيه للتعلم | Record routing decision for learning

        Args:
            service_name: اسم الخدمة | Service name
            instance: الـ instance المختار | Selected instance
            request_metadata: بيانات الطلب | Request metadata
        """
        self.routing_history[service_name].append(
            {
                "instance_id": instance.instance_id,
                "timestamp": datetime.now(),
                "request_metadata": request_metadata,
            }
        )

    def _calculate_instance_score(
        self, instance: ServiceInstance, request_metadata: dict | None = None
    ) -> float:
        """
        حساب score للـ instance بناءً على عدة عوامل
        """
        if not instance.metrics_history:
            return 0.5  # Neutral score for new instances

        latest_metrics = instance.metrics_history[-1]

        # Factor 1: Resource availability (higher is better)
        cpu_availability = 100 - latest_metrics.cpu_usage
        mem_availability = 100 - latest_metrics.memory_usage
        resource_score = (cpu_availability + mem_availability) / 200

        # Factor 2: Latency (lower is better)
        latency_score = max(0, 1.0 - (latest_metrics.latency_p95 / 1000))

        # Factor 3: Error rate (lower is better)
        error_score = max(0, 1.0 - (latest_metrics.error_rate / 100))

        # Factor 4: Load (lower is better for even distribution)
        load_score = max(0, 1.0 - (latest_metrics.active_connections / 1000))

        # Factor 5: Historical performance
        historical_score = self.instance_scores.get(instance.instance_id, 0.5)

        # Weighted combination
        return (
            resource_score * 0.3
            + latency_score * 0.25
            + error_score * 0.2
            + load_score * 0.15
            + historical_score * 0.1
        )


    def update_instance_score(self, instance_id: str, success: bool, response_time: float) -> None:
        """
        تحديث score الـ instance بناءً على نتيجة الطلب
        """
        current_score = self.instance_scores.get(instance_id, 0.5)

        # Calculate new score based on result
        if success and response_time < 200:  # Fast success
            adjustment = 0.05
        elif success:  # Slow success
            adjustment = 0.02
        else:  # Failure
            adjustment = -0.1

        # Update with learning rate
        new_score = current_score + (adjustment * 0.1)
        new_score = max(0.0, min(1.0, new_score))  # Clamp to [0, 1]

        self.instance_scores[instance_id] = new_score
