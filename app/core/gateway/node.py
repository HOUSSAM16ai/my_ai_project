"""
Neural Node Module.
Part of the Atomic Modularization Protocol.
"""

import asyncio
from dataclasses import dataclass, field

from app.core.gateway.circuit_breaker import CircuitBreaker

@dataclass
class NeuralNode:
    """
    Represents a single node in the AI Intelligence Mesh.
    Combines Model Identity with its Resilience State and Performance Metrics.
    """

    model_id: str
    circuit_breaker: CircuitBreaker

    # --- Performance Metrics (Legacy Cortex Memory - retained for logging) ---
    ewma_latency: float = 0.5

    # --- Smart Cooldown (V7.2: Adaptive) ---
    rate_limit_cooldown_until: float = 0.0
    consecutive_rate_limits: int = 0  # Track consecutive 429s for exponential backoff

    # --- Concurrency Control ---
    # Limit max concurrent streams to avoid provider rate limits
    semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(10))
