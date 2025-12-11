# app/services/model_serving_infrastructure.py
# ======================================================================================
# ==    MODEL SERVING INFRASTRUCTURE - BACKWARD COMPATIBILITY SHIM                   ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This file maintains backward compatibility by delegating to the refactored
#   hexagonal architecture in app/services/serving/
#
# SOLID PRINCIPLES APPLIED:
#   - Single Responsibility: Each component in serving/ has one clear purpose
#   - Open/Closed: Open for extension via ports/adapters
#   - Dependency Inversion: Depends on abstractions (ports)
#
# For new code, import directly from: app.services.serving
# This shim exists for backward compatibility only.

from __future__ import annotations

# Re-export everything from the refactored hexagonal architecture
from app.services.serving import (
    # Domain models
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
    # Application services
    ModelRegistry,
    InferenceRouter,
    ExperimentManager,
    # Infrastructure
    InMemoryModelRepository,
    InMemoryMetricsRepository,
    MockModelInvoker,
    # Facade and factory (backward compatibility)
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
    # Application services (for advanced usage)
    "ModelRegistry",
    "InferenceRouter",
    "ExperimentManager",
    # Infrastructure (for testing/mocking)
    "InMemoryModelRepository",
    "InMemoryMetricsRepository",
    "MockModelInvoker",
    # Main facade (most common usage)
    "ModelServingInfrastructure",
    "get_model_serving_infrastructure",
]
