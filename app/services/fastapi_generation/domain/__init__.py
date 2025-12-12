"""
Domain Layer - FastAPI Generation Service
=========================================
Pure business logic with no external dependencies.
"""
from .models import (
    CompletionRequest,
    GenerationRequest,
    GenerationResponse,
    OrchestratorConfig,
    OrchestratorTelemetry,
    StepState,
    StructuredJsonRequest,
)
from .ports import (
    ContextFinderPort,
    ErrorMessageBuilderPort,
    LLMClientPort,
    ModelSelectorPort,
    TaskExecutorPort,
)

__all__ = [
    # Models
    "StepState",
    "OrchestratorConfig",
    "OrchestratorTelemetry",
    "GenerationRequest",
    "GenerationResponse",
    "CompletionRequest",
    "StructuredJsonRequest",
    # Ports
    "LLMClientPort",
    "ModelSelectorPort",
    "ErrorMessageBuilderPort",
    "ContextFinderPort",
    "TaskExecutorPort",
]
