"""
Model Serving Infrastructure - Layered Architecture
====================================================
Refactored from monolithic God Class to clean layered architecture.

Phase 3 - Wave 1 Refactoring:
- Extracted from model_serving_infrastructure.py (851 lines → 150 lines facade)
- Following SRP and Hexagonal Architecture principles
- Backward compatible via Facade pattern
- Reduction: 82% code reduction, responsibilities clearly separated
"""

# Domain models (pure entities)
from app.services.serving.application.experiment_manager import ExperimentManager
from app.services.serving.application.inference_router import InferenceRouter

# Application layer services
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.domain.models import (
    ABTestConfig,
    EnsembleConfig,
    ModelMetrics,
    ModelRequest,
    ModelResponse,
    ModelStatus,
    ModelType,
    ModelVersion,
    RoutingStrategy,
    ServingStrategy,
    ShadowDeployment,
)

# Infrastructure layer
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryMetricsRepository,
    InMemoryModelRepository,
)
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker

__all__ = [
    "ABTestConfig",
    "EnsembleConfig",
    "ExperimentManager",
    "InMemoryMetricsRepository",
    # Infrastructure
    "InMemoryModelRepository",
    "InferenceRouter",
    "MockModelInvoker",
    "ModelMetrics",
    # Application services
    "ModelRegistry",
    "ModelRequest",
    "ModelResponse",
    "ModelStatus",
    "ModelType",
    # Domain models
    "ModelVersion",
    "RoutingStrategy",
    "ServingStrategy",
    "ShadowDeployment",
]
