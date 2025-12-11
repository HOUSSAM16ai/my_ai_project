# app/services/k8s/application/auto_scaler.py
"""Auto-scaling service"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.services.k8s.domain.models import AutoScalingConfig, Pod, PodPhase, ScalingDirection
from app.services.k8s.domain.ports import NodeRepositoryPort, PodRepositoryPort


class AutoScaler:
    """
    Auto-Scaler - Automatic horizontal pod scaling

    Responsibilities:
    - Monitor resource utilization
    - Scale deployments up/down based on thresholds
    - Respect cooldown periods
    """

    def __init__(
        self,
        pod_repo: PodRepositoryPort,
        node_repo: NodeRepositoryPort,
    ):
        self._pod_repo = pod_repo
        self._node_repo = node_repo
        self._configs: dict[str, AutoScalingConfig] = {}

    def configure_autoscaling(self, config: AutoScalingConfig) -> None:
        """Configure auto-scaling for a deployment"""
        self._configs[config.deployment_name] = config

    def check_autoscaling(self) -> None:
        """Check all deployments and apply scaling if needed"""
        for config in self._configs.values():
            self._check_deployment_scaling(config)

    def _check_deployment_scaling(self, config: AutoScalingConfig) -> None:
        """Check if a deployment needs scaling"""
        # Get deployment pods
        pods = [
            p
            for p in self._pod_repo.list_pods(config.namespace)
            if p.name.startswith(config.deployment_name) and p.phase == PodPhase.RUNNING
        ]

        if not pods:
            return

        # Calculate average utilization
        cpu_usage = self._calculate_deployment_cpu_usage(pods)
        memory_usage = self._calculate_deployment_memory_usage(pods)

        # Determine scaling direction
        direction = ScalingDirection.NONE

        if cpu_usage > config.target_cpu_utilization or memory_usage > config.target_memory_utilization:
            if len(pods) < config.max_replicas:
                direction = ScalingDirection.UP
        elif (
            cpu_usage < config.target_cpu_utilization * 0.5
            and memory_usage < config.target_memory_utilization * 0.5
        ):
            if len(pods) > config.min_replicas:
                direction = ScalingDirection.DOWN

        # Check cooldown
        if direction != ScalingDirection.NONE:
            if self._is_cooldown_active(config, direction):
                return

            self.scale_deployment(config, direction)

    def scale_deployment(self, config: AutoScalingConfig, direction: ScalingDirection) -> None:
        """Scale a deployment up or down"""
        pods = [
            p
            for p in self._pod_repo.list_pods(config.namespace)
            if p.name.startswith(config.deployment_name)
        ]

        if direction == ScalingDirection.UP:
            # Create new pod
            new_pod = Pod(
                pod_id=str(uuid.uuid4()),
                name=f"{config.deployment_name}-{len(pods) + 1}",
                namespace=config.namespace,
                node_id="",  # Will be assigned by scheduler
                phase=PodPhase.PENDING,
                container_image="app:latest",
            )
            self._pod_repo.save_pod(new_pod)

        elif direction == ScalingDirection.DOWN:
            # Remove one pod
            if pods:
                pod_to_remove = pods[-1]
                self._pod_repo.delete_pod(pod_to_remove.pod_id)

        # Update last scale time
        config.last_scale_time = datetime.now(UTC)

    def _calculate_deployment_cpu_usage(self, pods: list[Pod]) -> float:
        """Calculate average CPU usage for deployment"""
        if not pods:
            return 0.0

        total_usage = sum(p.cpu_request for p in pods)
        total_limit = sum(p.cpu_limit for p in pods)

        return (total_usage / total_limit * 100) if total_limit > 0 else 0.0

    def _calculate_deployment_memory_usage(self, pods: list[Pod]) -> float:
        """Calculate average memory usage for deployment"""
        if not pods:
            return 0.0

        total_usage = sum(p.memory_request for p in pods)
        total_limit = sum(p.memory_limit for p in pods)

        return (total_usage / total_limit * 100) if total_limit > 0 else 0.0

    def _is_cooldown_active(self, config: AutoScalingConfig, direction: ScalingDirection) -> bool:
        """Check if cooldown period is active"""
        if not config.last_scale_time:
            return False

        elapsed = (datetime.now(UTC) - config.last_scale_time).total_seconds()

        if direction == ScalingDirection.UP:
            return elapsed < config.scale_up_cooldown
        else:
            return elapsed < config.scale_down_cooldown
