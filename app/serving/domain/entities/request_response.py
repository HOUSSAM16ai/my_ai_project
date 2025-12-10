"""
Request and Response Entities
==============================
Domain entities for model requests and responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class RoutingStrategy(Enum):
    """استراتيجيات التوجيه"""

    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"
    WEIGHTED = "weighted"
    INTELLIGENT = "intelligent"  # ML-based routing


@dataclass
class ModelRequest:
    """طلب للنموذج"""

    request_id: str
    model_id: str
    version_id: str
    input_data: dict[str, Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    routing_strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN


@dataclass
class ModelResponse:
    """استجابة من النموذج"""

    request_id: str
    model_id: str
    version_id: str
    output_data: Any
    latency_ms: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    error: str | None = None
