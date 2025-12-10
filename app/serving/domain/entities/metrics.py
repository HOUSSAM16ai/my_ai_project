"""
Model Metrics Entity
====================
Domain entity for model performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ModelMetrics:
    """مقاييس أداء النموذج"""

    version_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    tokens_processed: int = 0
    cost_usd: float = 0.0
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_usage: float = 0.0
