# app/services/serving/domain/models.py
"""
Domain Models for Model Serving Infrastructure
===============================================
Pure domain entities with zero infrastructure dependencies.

Extracted from model_serving_infrastructure.py (Phase 3 - Wave 1)
Following Domain-Driven Design principles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================

class ModelStatus(Enum):
    """حالات النموذج"""

    LOADING = "loading"
    READY = "ready"
    SERVING = "serving"
    DRAINING = "draining"  # يستنزف الطلبات الحالية قبل الإيقاف
    STOPPED = "stopped"
    FAILED = "failed"

class ServingStrategy(Enum):
    """استراتيجيات التقديم"""

    SINGLE = "single"  # نموذج واحد فقط
    AB_TESTING = "ab_testing"  # اختبار A/B
    CANARY = "canary"  # نشر تدريجي
    SHADOW = "shadow"  # وضع خفي (جمع بيانات فقط)
    MULTI_MODEL = "multi_model"  # نماذج متعددة مع توجيه ذكي
    ENSEMBLE = "ensemble"  # تجميع نتائج نماذج متعددة

class ModelType(Enum):
    """أنواع النماذج"""

    LANGUAGE_MODEL = "language_model"  # نماذج اللغة (GPT, Claude, etc.)
    VISION_MODEL = "vision_model"  # نماذج الرؤية
    EMBEDDING_MODEL = "embedding_model"  # نماذج التضمين
    CUSTOM_MODEL = "custom_model"  # نماذج مخصصة

class RoutingStrategy(Enum):
    """استراتيجيات التوجيه"""

    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"
    WEIGHTED = "weighted"
    INTELLIGENT = "intelligent"  # ML-based routing

# ======================================================================================
# DOMAIN ENTITIES
# ======================================================================================

@dataclass
class ModelVersion:
    """
    نسخة من النموذج

    Entity representing a specific version of a model.
    Immutable after creation (except status transitions).
    """

    version_id: str
    model_name: str
    version_number: str
    model_type: ModelType
    status: ModelStatus
    endpoint: str | None = None
    framework: str = "pytorch"  # pytorch, tensorflow, onnx
    device: str = "cpu"  # cpu, cuda, mps
    batch_size: int = 1
    max_sequence_length: int = 2048
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    loaded_at: datetime | None = None

@dataclass
class ModelMetrics:
    """
    مقاييس أداء النموذج

    Value Object containing performance metrics snapshot.
    """

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

@dataclass
class ABTestConfig:
    """
    تكوين اختبار A/B

    Entity representing an A/B test configuration.
    """

    test_id: str
    model_a_id: str
    model_b_id: str
    model_a_percentage: float = 50.0
    model_b_percentage: float = 50.0
    duration_hours: int = 24
    success_metric: str = "latency"  # latency, accuracy, cost
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    winner: str | None = None

@dataclass
class ShadowDeployment:
    """
    نشر في الوضع الخفي

    Entity for shadow deployment configuration.
    """

    shadow_id: str
    primary_model_id: str
    shadow_model_id: str
    traffic_percentage: float = 100.0  # نسبة الطلبات لنسخها للوضع الخفي
    collect_responses: bool = True
    compare_results: bool = True
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    comparison_results: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class ModelRequest:
    """
    طلب للنموذج

    Value Object representing an inference request.
    """

    request_id: str
    model_id: str
    version_id: str
    input_data: dict[str, Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass
class ModelResponse:
    """
    استجابة النموذج

    Value Object representing an inference response.
    """

    request_id: str
    model_id: str
    version_id: str
    output_data: Any
    latency_ms: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass
class EnsembleConfig:
    """
    تكوين التجميع (Ensemble)

    Configuration for ensemble serving strategy.
    """

    ensemble_id: str
    model_ids: list[str]
    aggregation_method: str = "voting"  # voting, averaging, weighted
    weights: dict[str, float] = field(default_factory=dict)
