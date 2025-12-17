# app/services/orchestration/application/auto_scaler.py
"""
Auto Scaler Service
===================
Single Responsibility: Automatic horizontal pod scaling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.services.orchestration.domain.models import AutoScalingConfig, ScalingDirection


class PodRepository(Protocol):
    def get_all(self) -> list: ...


class AutoScaler:
    """
    Kubernetes auto-scaler.

    Responsibilities:
    - Monitor resource usage
    - Scale deployments up/down
    - Respect min/max replicas
    """

    def __init__(self, pod_repository: PodRepository):
        self._pod_repo = pod_repository
        self._configs: dict[str, AutoScalingConfig] = {}
        self._last_scale_time: dict[str, datetime] = {}

    def configure_autoscaling(
        self,
        deployment_name: str,
        min_replicas: int,
        max_replicas: int,
        target_cpu_percent: float,
        target_memory_percent: float = 80.0,
    ) -> None:
        """Configure auto-scaling for deployment"""
        config = AutoScalingConfig(
            deployment_name=deployment_name,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            target_cpu_percent=target_cpu_percent,
            target_memory_percent=target_memory_percent,
        )
        self._configs[deployment_name] = config

    def check_autoscaling(self, deployment_name: str) -> tuple[ScalingDirection, int]:
        """Check if scaling is needed"""
        if deployment_name not in self._configs:
            return ScalingDirection.NONE, 0

        config = self._configs[deployment_name]

        # Check cooldown period
        if not self._can_scale(deployment_name, config):
            return ScalingDirection.NONE, 0

        # Calculate current resource usage
        cpu_usage = self._calculate_deployment_cpu_usage(deployment_name)
        current_replicas = self._get_current_replicas(deployment_name)

        # Determine scaling direction
        if cpu_usage > config.target_cpu_percent * config.scale_up_threshold:
            # Scale up
            new_replicas = min(current_replicas + 1, config.max_replicas)
            if new_replicas > current_replicas:
                self._last_scale_time[deployment_name] = datetime.utcnow()
                return ScalingDirection.UP, new_replicas

        elif cpu_usage < config.target_cpu_percent * config.scale_down_threshold:
            # Scale down
            new_replicas = max(current_replicas - 1, config.min_replicas)
            if new_replicas < current_replicas:
                self._last_scale_time[deployment_name] = datetime.utcnow()
                return ScalingDirection.DOWN, new_replicas

        return ScalingDirection.NONE, current_replicas

    def _can_scale(self, deployment_name: str, config: AutoScalingConfig) -> bool:
        """Check if cooldown period has passed"""
        if deployment_name not in self._last_scale_time:
            return True

        last_scale = self._last_scale_time[deployment_name]
        elapsed = (datetime.utcnow() - last_scale).total_seconds()

        return elapsed >= config.cooldown_seconds

    def _calculate_deployment_cpu_usage(self, deployment_name: str) -> float:
        """Calculate average CPU usage for deployment"""
        # Simplified: in production, query actual metrics
        # For now, simulate with random value
        import random
        return random.uniform(20, 90)

    def _get_current_replicas(self, deployment_name: str) -> int:
        """Get current replica count"""
        # Simplified: count pods with matching label
        pods = self._pod_repo.get_all()
        return len([p for p in pods if deployment_name in p.labels.get("app", "")])
