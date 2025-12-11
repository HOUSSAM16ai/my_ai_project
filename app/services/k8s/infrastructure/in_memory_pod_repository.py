# app/services/k8s/infrastructure/in_memory_pod_repository.py
"""In-memory Pod repository implementation"""

from __future__ import annotations

import threading

from app.services.k8s.domain.models import Pod, PodPhase


class InMemoryPodRepository:
    """In-memory storage for Pods"""

    def __init__(self):
        self._pods: dict[str, Pod] = {}
        self._lock = threading.RLock()

    def save_pod(self, pod: Pod) -> None:
        """Save a pod"""
        with self._lock:
            self._pods[pod.pod_id] = pod

    def get_pod(self, pod_id: str) -> Pod | None:
        """Get pod by ID"""
        with self._lock:
            return self._pods.get(pod_id)

    def list_pods(self, namespace: str | None = None) -> list[Pod]:
        """List all pods, optionally filtered by namespace"""
        with self._lock:
            if namespace:
                return [p for p in self._pods.values() if p.namespace == namespace]
            return list(self._pods.values())

    def delete_pod(self, pod_id: str) -> bool:
        """Delete a pod"""
        with self._lock:
            if pod_id in self._pods:
                del self._pods[pod_id]
                return True
            return False

    def update_pod_phase(self, pod_id: str, phase: PodPhase) -> None:
        """Update pod phase"""
        with self._lock:
            if pod_id in self._pods:
                self._pods[pod_id].phase = phase
