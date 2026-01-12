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
from typing import Any

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
            return [m for m in self._models.values() if m.model_name == model_name]

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

    def get_summary(self, version_id: str) -> dict[str, Any]:
        """
        Get aggregated metrics summary
        الحصول على ملخص المقاييس المجمعة

        Args:
            version_id: معرف نسخة النموذج | Model version ID

        Returns:
            ملخص المقاييس | Metrics summary
        """
        with self._lock:
            metrics_list = list(self._metrics.get(version_id, []))

            if not metrics_list:
                return self._create_empty_summary()

            return self._calculate_metrics_summary(metrics_list)

    def _create_empty_summary(self) -> dict[str, Any]:
        """
        إنشاء ملخص فارغ | Create empty summary

        Returns:
            ملخص فارغ | Empty summary
        """
        return {
            "total_requests": 0,
            "avg_latency": 0.0,
            "total_cost": 0.0,
            "success_rate": 0.0,
        }

    def _calculate_metrics_summary(self, metrics_list: list[ModelMetrics]) -> dict[str, Any]:
        """
        حساب ملخص المقاييس | Calculate metrics summary

        Args:
            metrics_list: قائمة المقاييس | Metrics list

        Returns:
            الملخص المحسوب | Calculated summary
        """
        total_requests = sum(m.total_requests for m in metrics_list)
        successful_requests = sum(m.successful_requests for m in metrics_list)

        avg_latency = self._calculate_average_latency(metrics_list)
        total_cost = sum(m.cost_usd for m in metrics_list)
        success_rate = self._calculate_success_rate(total_requests, successful_requests)

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "avg_latency": avg_latency,
            "total_cost": total_cost,
            "success_rate": success_rate,
        }

    def _calculate_average_latency(self, metrics_list: list[ModelMetrics]) -> float:
        """
        حساب متوسط زمن الاستجابة | Calculate average latency

        Args:
            metrics_list: قائمة المقاييس | Metrics list

        Returns:
            متوسط زمن الاستجابة | Average latency
        """
        if not metrics_list:
            return 0.0
        return sum(m.avg_latency_ms for m in metrics_list) / len(metrics_list)

    def _calculate_success_rate(self, total_requests: int, successful_requests: int) -> float:
        """
        حساب معدل النجاح | Calculate success rate

        Args:
            total_requests: إجمالي الطلبات | Total requests
            successful_requests: الطلبات الناجحة | Successful requests

        Returns:
            معدل النجاح | Success rate
        """
        if total_requests == 0:
            return 0.0
        return successful_requests / total_requests * 100
