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

# Application layer services
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.application.inference_router import InferenceRouter
from app.services.serving.application.experiment_manager import ExperimentManager

# Infrastructure layer
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryModelRepository,
    InMemoryMetricsRepository,
)
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker

# Facade for backward compatibility
from app.services.serving.facade import (
    ModelServingInfrastructure,
    get_model_serving_infrastructure,
)

__all__ = [
    # Domain models
    "ModelVersion",
    "ModelMetrics",
    "ModelRequest",
    "ModelResponse",
    "ABTestConfig",
    "ShadowDeployment",
    "EnsembleConfig",
    "ModelStatus",
    "ModelType",
    "ServingStrategy",
    "RoutingStrategy",
    # Application services
    "ModelRegistry",
    "InferenceRouter",
    "ExperimentManager",
    # Infrastructure
    "InMemoryModelRepository",
    "InMemoryMetricsRepository",
    "MockModelInvoker",
    # Facade (backward compatibility)
    "ModelServingInfrastructure",
    "get_model_serving_infrastructure",
]
