# app/services/serving/infrastructure/in_memory_repository.py
"""
In-Memory Model Repository Implementation
==========================================
Simple in-memory implementation for model storage.

Can be replaced with Redis/Database implementation without changing application logic.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque

from app.services.serving.domain.models import ModelMetrics, ModelVersion

class InMemoryModelRepository:
    """
    In-memory implementation of ModelRepository port.

    Thread-safe storage using RLock.
    Suitable for single-instance deployments or testing.
    """

    def __init__(self):
        self._models: dict[str, ModelVersion] = {}
        self._lock = threading.RLock()

    def save(self, model: ModelVersion) -> bool:
        """Save a model version"""
        with self._lock:
            if model.version_id in self._models:
                return False  # Already exists
            self._models[model.version_id] = model
            return True

    def get(self, version_id: str) -> ModelVersion | None:
        """Retrieve a model by ID"""
        with self._lock:
            return self._models.get(version_id)

    def list_by_name(self, model_name: str) -> list[ModelVersion]:
        """List all versions of a model"""
        with self._lock:
            return [
                m for m in self._models.values()
                if m.model_name == model_name
            ]

    def delete(self, version_id: str) -> bool:
        """Remove a model"""
        with self._lock:
            if version_id not in self._models:
                return False
            del self._models[version_id]
            return True

    def list_all(self) -> list[ModelVersion]:
        """List all models"""
        with self._lock:
            return list(self._models.values())

    def update(self, model: ModelVersion) -> bool:
        """Update an existing model"""
        with self._lock:
            if model.version_id not in self._models:
                return False
            self._models[model.version_id] = model
            return True

class InMemoryMetricsRepository:
    """
    In-memory implementation of MetricsRepository port.

    Stores metrics in a circular buffer (deque) per model.
    Limited history to prevent memory overflow.
    """

    def __init__(self, max_history: int = 10000):
        self._metrics: dict[str, deque[ModelMetrics]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._lock = threading.RLock()

    def record(self, metrics: ModelMetrics) -> None:
        """Record metrics snapshot"""
        with self._lock:
            self._metrics[metrics.version_id].append(metrics)

    def get_recent(self, version_id: str, limit: int = 100) -> list[ModelMetrics]:
        """Get recent metrics for a model"""
        with self._lock:
            all_metrics = list(self._metrics.get(version_id, []))
            return all_metrics[-limit:] if all_metrics else []

    # TODO: Split this function (31 lines) - KISS principle
    def get_summary(self, version_id: str) -> dict[str, Any]:
        """Get aggregated metrics summary"""
        with self._lock:
            metrics_list = list(self._metrics.get(version_id, []))

            if not metrics_list:
                return {
                    "total_requests": 0,
                    "avg_latency": 0.0,
                    "total_cost": 0.0,
                    "success_rate": 0.0,
                }

            total_requests = sum(m.total_requests for m in metrics_list)
            successful_requests = sum(m.successful_requests for m in metrics_list)
            avg_latency = (
                sum(m.avg_latency_ms for m in metrics_list) / len(metrics_list)
                if metrics_list else 0.0
            )
            total_cost = sum(m.cost_usd for m in metrics_list)
            success_rate = (
                successful_requests / total_requests * 100
                if total_requests > 0 else 0.0
            )

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "avg_latency": avg_latency,
                "total_cost": total_cost,
                "success_rate": success_rate,
            }
