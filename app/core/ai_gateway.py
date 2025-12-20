"""
Ai Gateway

هذا الملف جزء من مشروع CogniForge.
"""

# app/core/ai_gateway.py
"""
The ENERGY-ENGINE (V7.2 - SUPERHUMAN EDITION - ULTRA-OPTIMIZED).

This file now serves as a FACADE for the atomic modules located in `app/core/gateway/`.
This maintains backward compatibility while enforcing SRP via the new structure.
"""

import logging
from typing import Any

from app.core.gateway.circuit_breaker import CircuitBreaker, CircuitState
from app.core.gateway.connection import ConnectionManager

# --- Import Atomic Modules ---
from app.core.gateway.exceptions import (
    AIAllModelsExhaustedError,
    AICircuitOpenError,
    AIConnectionError,
    AIError,
    AIProviderError,
    AIRateLimitError,
)
from app.core.gateway.mesh import AIClient, NeuralRoutingMesh, get_ai_client
from app.core.gateway.node import NeuralNode
from app.core.superhuman_performance_optimizer import get_performance_optimizer

# Re-export key components for backward compatibility
__all__ = [
    "AIAllModelsExhaustedError",
    "AICircuitOpenError",
    "AIClient",
    "AIConnectionError",
    "AIError",
    "AIProviderError",
    "AIRateLimitError",
    "CircuitBreaker",
    "CircuitState",
    "ConnectionManager",
    "NeuralNode",
    "NeuralRoutingMesh",
    "get_ai_client",
    "get_performance_report",
    "get_recommended_model",
]

logger = logging.getLogger(__name__)
_performance_optimizer = get_performance_optimizer()


def get_performance_report() -> dict[str, "Any"]:
    """
    Get comprehensive performance report from the optimizer.
    Delegates to the optimizer service.
    """
    return _performance_optimizer.get_detailed_report()


def get_recommended_model(available_models: list[str], context: str = "") -> str:
    """
    Get AI-recommended model based on historical performance.
    Delegates to the optimizer service.
    """
    return _performance_optimizer.get_recommended_model(available_models, context)
