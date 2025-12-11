# app/ai/domain/__init__.py
"""
LLM Client Domain Layer
========================
Pure domain logic without external dependencies.

Following Domain-Driven Design (DDD):
- Rich domain models
- Clear boundaries
- Business logic encapsulation
"""

from app.ai.domain.models import (
    CircuitBreakerStats,
    CircuitState,
    CostRecord,
    ErrorCategory,
    LLMProvider,
    LLMRequest,
    Message,
    MessageRole,
    ModelResponse,
    TokenUsage,
)

__all__ = [
    # Enums
    "LLMProvider",
    "MessageRole",
    "ErrorCategory",
    "CircuitState",
    # Value Objects
    "Message",
    "TokenUsage",
    "ModelResponse",
    # Entities
    "LLMRequest",
    "CostRecord",
    "CircuitBreakerStats",
]
