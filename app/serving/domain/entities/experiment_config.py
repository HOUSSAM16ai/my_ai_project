"""
Experiment Configuration Entities
=================================
Domain entities for A/B testing, shadow deployment, and ensemble configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ServingStrategy(Enum):
    """استراتيجيات التقديم"""

    SINGLE = "single"  # نموذج واحد فقط
    AB_TESTING = "ab_testing"  # اختبار A/B
    CANARY = "canary"  # نشر تدريجي
    SHADOW = "shadow"  # وضع خفي (جمع بيانات فقط)
    MULTI_MODEL = "multi_model"  # نماذج متعددة مع توجيه ذكي
    ENSEMBLE = "ensemble"  # تجميع نتائج نماذج متعددة


@dataclass
class ABTestConfig:
    """تكوين اختبار A/B"""

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
    """نشر في الوضع الخفي"""

    shadow_id: str
    primary_model_id: str
    shadow_model_id: str
    traffic_percentage: float = 100.0  # نسبة الطلبات لنسخها للوضع الخفي
    collect_responses: bool = True
    compare_results: bool = True
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    comparison_results: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EnsembleConfig:
    """تكوين تجميع النماذج"""

    ensemble_id: str
    model_versions: list[str]
    aggregation_method: str = "voting"  # voting, averaging, stacking
    weights: dict[str, float] = field(default_factory=dict)
    min_agreements: int = 2
