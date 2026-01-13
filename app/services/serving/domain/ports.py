# app/services/serving/domain/ports.py
"""
Domain Ports (Interfaces) for Model Serving
============================================
Protocols defining contracts for infrastructure adapters.

Following Hexagonal Architecture / Ports & Adapters pattern.
"""

from __future__ import annotations

from typing import Protocol

from app.services.serving.domain.models import (
    ModelMetrics,
    ModelRequest,
    ModelResponse,
    ModelVersion,
)

# ======================================================================================
# REPOSITORY PORTS
# ======================================================================================


class ModelRepository(Protocol):
    """
    Port for model storage and retrieval.

    Infrastructure implementations:
    - InMemoryModelRepository
    - RedisModelRepository
    - DatabaseModelRepository
    """

    def save(self, model: ModelVersion) -> bool:
        """Save a model version"""
        ...

    def get(self, version_id: str) -> ModelVersion | None:
        """Retrieve a model by ID"""
        ...

    def list_by_name(self, model_name: str) -> list[ModelVersion]:
        """List all versions of a model"""
        ...

    def delete(self, version_id: str) -> bool:
        """Remove a model"""
        ...

    def list_all(self) -> list[ModelVersion]:
        """List all models"""
        ...


class MetricsRepository(Protocol):
    """
    Port for metrics storage.

    Infrastructure implementations:
    - InMemoryMetricsRepository
    - TimeSeriesMetricsRepository (Prometheus, InfluxDB)
    """

    def record(self, metrics: ModelMetrics) -> None:
        """Record metrics snapshot"""
        ...

    def get_recent(self, version_id: str, limit: int = 100) -> list[ModelMetrics]:
        """Get recent metrics for a model"""
        ...

    def get_summary(self, version_id: str) -> dict[str, object]:
        """Get aggregated metrics summary"""
        ...


# ======================================================================================
# INFERENCE PORTS
# ======================================================================================


class ModelInvoker(Protocol):
    """
    Port for actual model inference.

    Infrastructure implementations:
    - OpenAIModelInvoker
    - TorchServeInvoker
    - TensorFlowServingInvoker
    - LocalModelInvoker
    """

    def invoke(
        self,
        model: ModelVersion,
        request: ModelRequest,
    ) -> ModelResponse:
        """Execute inference on a model"""
        ...

    def health_check(self, model: ModelVersion) -> bool:
        """Check if model is healthy and ready"""
        ...


class CostCalculator(Protocol):
    """
    Port for cost calculation.

    Different pricing strategies for different providers.
    """

    def calculate_cost(
        self,
        model: ModelVersion,
        request: ModelRequest,
        response: ModelResponse,
    ) -> float:
        """Calculate the cost of an inference request"""
        ...


# ======================================================================================
# ORCHESTRATION PORTS
# ======================================================================================


class LoadBalancer(Protocol):
    """
    Port for load balancing strategies.

    Implementations:
    - RoundRobinBalancer
    - LeastLatencyBalancer
    - WeightedBalancer
    """

    def select_model(
        self,
        available_models: list[ModelVersion],
        request: ModelRequest,
    ) -> ModelVersion:
        """Select the best model for a request"""
        ...
