# app/ai/infrastructure/__init__.py
"""
LLM Client Infrastructure Layer
================================
Concrete implementations of domain ports.

Adapters for external services and systems:
- Transports for LLM providers
- Cache implementations
- Metrics and observability
"""

from app.ai.infrastructure.cache import (
    DiskCache,
    InMemoryCache,
    NoOpCache,
    get_cache,
    reset_cache,
)
from app.ai.infrastructure.metrics import (
    InMemoryMetrics,
    SimpleObserver,
    Span,
    get_metrics,
    get_observer,
    reset_observability,
)
from app.ai.infrastructure.transports import (
    MockLLMTransport,
    OpenRouterTransport,
    create_llm_transport,
    get_transport,
    register_transport,
)

__all__ = [
    # Transports
    "OpenRouterTransport",
    "MockLLMTransport",
    "create_llm_transport",
    "get_transport",
    "register_transport",
    # Cache
    "InMemoryCache",
    "DiskCache",
    "NoOpCache",
    "get_cache",
    "reset_cache",
    # Metrics & Observability
    "InMemoryMetrics",
    "SimpleObserver",
    "Span",
    "get_metrics",
    "get_observer",
    "reset_observability",
]
