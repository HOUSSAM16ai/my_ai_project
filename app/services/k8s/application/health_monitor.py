# app/services/k8s/application/health_monitor.py
"""Health monitoring service"""

from __future__ import annotations

import random
import threading
import time
from datetime import UTC, datetime, timedelta

from app.services.k8s.domain.models import NodeState, PodPhase
from app.services.k8s.domain.ports import NodeRepositoryPort, PodRepositoryPort


class HealthMonitor:
    """
    Health Monitor - Continuous health checking

    Responsibilities:
    - Monitor pod health
    - Monitor node health
    - Trigger healing when issues detected
    """

    def __init__(
        self,
        pod_repo: PodRepositoryPort,
        node_repo: NodeRepositoryPort,
        on_pod_failure=None,
        on_node_failure=None,
    ):
        self._pod_repo = pod_repo
        self._node_repo = node_repo
        self._on_pod_failure = on_pod_failure
        self._on_node_failure = on_node_failure
        self._monitoring = False

    def start_monitoring(self) -> None:
        """Start continuous health monitoring"""
        if self._monitoring:
            return

        self._monitoring = True

        def monitor():
            while self._monitoring:
                try:
                    self.check_pod_health()
                    self.check_node_health()
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    print(f"Health monitoring error: {e}")

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def stop_monitoring(self) -> None:
        """Stop health monitoring"""
        self._monitoring = False

    def check_pod_health(self) -> None:
        """Check health of all pods"""
        pods = self._pod_repo.list_pods()

        for pod in pods:
            if pod.phase != PodPhase.RUNNING:
                continue

            # Simulate random pod failures (1% chance)
            if random.random() < 0.01:
                pod.phase = PodPhase.FAILED
                self._pod_repo.update_pod_phase(pod.pod_id, PodPhase.FAILED)

                # Trigger healing callback
                if self._on_pod_failure:
                    self._on_pod_failure(pod)

    def check_node_health(self) -> None:
        """Check health of all nodes"""
        nodes = self._node_repo.list_nodes()

        for node in nodes:
            if node.state != NodeState.READY:
                continue

            # Check heartbeat timeout
            time_since_heartbeat = datetime.now(UTC) - node.last_heartbeat

            if time_since_heartbeat > timedelta(seconds=30):
                # Node is unhealthy
                node.state = NodeState.NOT_READY
                self._node_repo.save_node(node)

                # Trigger healing callback
                if self._on_node_failure:
                    self._on_node_failure(node)
