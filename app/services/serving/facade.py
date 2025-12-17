# app/services/serving/facade.py
"""
Model Serving Infrastructure - Backward Compatible Facade
==========================================================
Thin facade maintaining backward compatibility with original API.

This file delegates to the refactored layered architecture:
- Domain models in domain/
- Application services in application/
- Infrastructure adapters in infrastructure/

Original file: model_serving_infrastructure.py (851 lines)
Refactored size: ~150 lines (facade only)
"""

from __future__ import annotations

import threading
from typing import Any

from app.services.serving.domain.models import (
    ABTestConfig,
    ModelResponse,
    ModelVersion,
)
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.application.inference_router import InferenceRouter
from app.services.serving.application.experiment_manager import ExperimentManager
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryModelRepository,
    InMemoryMetricsRepository,
)
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker


class ModelServingInfrastructure:
    """
    Facade for Model Serving Infrastructure.

    **REFACTORED**: This class now delegates to specialized services
    instead of implementing everything inline.

    Maintains 100% backward compatibility with original API while
    using clean layered architecture internally.

    Original responsibilities (851 lines) now delegated to:
    - ModelRegistry: Model lifecycle management
    - InferenceRouter: Request routing and execution
    - ExperimentManager: A/B tests, shadow deployments, ensembles
    - Repositories: Data storage
    - Invokers: Actual model execution
    """

    def __init__(self):
        """Initialize facade with composed services."""
        # Infrastructure layer
        self._model_repo = InMemoryModelRepository()
        self._metrics_repo = InMemoryMetricsRepository()
        self._invoker = MockModelInvoker()

        # Application layer
        self._registry = ModelRegistry(self._model_repo)
        self._router = InferenceRouter(
            self._registry,
            self._invoker,
            self._metrics_repo,
        )
        self._experiment_manager = ExperimentManager(
            self._registry,
            self._router,
        )

        # Legacy compatibility fields (kept for backward compat)
        self._lock = threading.RLock()

    # ======================================================================================
    # MODEL MANAGEMENT (delegates to ModelRegistry)
    # ======================================================================================

    def register_model(self, model: ModelVersion) -> bool:
        """Register a new model version."""
        return self._registry.register_model(model)

    def unload_model(self, version_id: str) -> bool:
        """Unload a model."""
        return self._registry.unload_model(version_id)

    def get_model_status(self, version_id: str) -> ModelVersion | None:
        """Get model status."""
        return self._registry.get_model(version_id)

    def list_models(self) -> list[ModelVersion]:
        """List all registered models."""
        return self._registry.list_models()

    # ======================================================================================
    # MODEL SERVING (delegates to InferenceRouter)
    # ======================================================================================

    def serve_request(
        self,
        model_name: str,
        input_data: dict[str, Any],
        version_id: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """Serve an inference request."""
        return self._router.serve_request(
            model_name,
            input_data,
            version_id,
            parameters,
        )

    # ======================================================================================
    # A/B TESTING (delegates to ExperimentManager)
    # ======================================================================================

    def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        split_percentage: float = 50.0,
        duration_hours: int = 24,
    ) -> str:
        """Start an A/B test."""
        return self._experiment_manager.start_ab_test(
            model_a_id,
            model_b_id,
            split_percentage,
            duration_hours,
        )

    def serve_ab_test_request(
        self,
        test_id: str,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """Serve request within A/B test."""
        return self._experiment_manager.serve_ab_test_request(
            test_id,
            input_data,
            parameters,
        )

    def analyze_ab_test(self, test_id: str) -> dict[str, Any]:
        """Analyze A/B test results."""
        return self._experiment_manager.analyze_ab_test(test_id)

    def get_ab_test_status(self, test_id: str) -> ABTestConfig | None:
        """Get A/B test configuration."""
        return self._experiment_manager.get_ab_test(test_id)

    # ======================================================================================
    # SHADOW MODE (delegates to ExperimentManager)
    # ======================================================================================

    def start_shadow_deployment(
        self,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float = 100.0,
    ) -> str:
        """Start shadow deployment."""
        return self._experiment_manager.start_shadow_deployment(
            primary_model_id,
            shadow_model_id,
            traffic_percentage,
        )

    def get_shadow_deployment_stats(self, shadow_id: str) -> dict[str, Any] | None:
        """Get shadow deployment stats."""
        deployment = self._experiment_manager.get_shadow_deployment(shadow_id)
        if not deployment:
            return None

        return {
            "shadow_id": shadow_id,
            "primary_model": deployment.primary_model_id,
            "shadow_model": deployment.shadow_model_id,
            "comparisons_count": len(deployment.comparison_results),
            "recent_comparisons": deployment.comparison_results[-10:],
        }


# ======================================================================================
# SINGLETON INSTANCE (backward compatibility)
# ======================================================================================

_model_serving_instance: ModelServingInfrastructure | None = None
_model_serving_lock = threading.Lock()


def get_model_serving_infrastructure() -> ModelServingInfrastructure:
    """Get singleton instance of model serving infrastructure."""
    global _model_serving_instance

    if _model_serving_instance is None:
        with _model_serving_lock:
            if _model_serving_instance is None:
                _model_serving_instance = ModelServingInfrastructure()

    return _model_serving_instance
