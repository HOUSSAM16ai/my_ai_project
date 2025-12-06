"""Design patterns implementations."""

from .chain_of_responsibility import (
    AuthenticationHandler,
    AuthorizationHandler,
    Handler,
    RateLimitHandler,
    RequestContext,
    ValidationHandler,
    build_request_pipeline,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState, circuit_breaker
from .dependency_injection import DIContainer, get_container, inject
from .event_bus import Event, EventBus, get_event_bus

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "circuit_breaker",
    "Event",
    "EventBus",
    "get_event_bus",
    "DIContainer",
    "get_container",
    "inject",
    "Handler",
    "RequestContext",
    "AuthenticationHandler",
    "AuthorizationHandler",
    "RateLimitHandler",
    "ValidationHandler",
    "build_request_pipeline",
]
