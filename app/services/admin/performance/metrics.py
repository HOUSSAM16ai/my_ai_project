"""نماذج أداء المحادثات الإدارية ومحددات التصنيف المرتبطة بها."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class PerformanceCategory(Enum):
    """فئات الأداء المعتمدة لتصنيف زمن الاستجابة."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    SLOW = "slow"


class ABTestVariant(Enum):
    """متغيرات اختبارات A/B المعتمدة في خدمة الأداء."""

    STREAMING_ENABLED = "streaming_enabled"
    STREAMING_DISABLED = "streaming_disabled"
    CHUNK_SIZE_3 = "chunk_size_3"
    CHUNK_SIZE_5 = "chunk_size_5"
    CHUNK_SIZE_1 = "chunk_size_1"


@dataclass(slots=True)
class PerformanceMetric:
    """مقياس أداء مفرد يلتقط بيانات الاستجابة في لحظة زمنية."""

    metric_id: str
    category: str
    latency_ms: float
    tokens: int
    model_used: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id: int | None = None

    def get_category(self) -> PerformanceCategory:
        """يعيد الفئة المناسبة بناءً على زمن الاستجابة المسجل."""
        if self.latency_ms < 500:
            return PerformanceCategory.EXCELLENT
        if self.latency_ms < 1000:
            return PerformanceCategory.GOOD
        if self.latency_ms < 3000:
            return PerformanceCategory.ACCEPTABLE
        return PerformanceCategory.SLOW


@dataclass(slots=True)
class MetricRecordConfig:
    """إعدادات تسجيل المقياس مع خيارات اختبار A/B."""

    category: str
    latency_ms: float
    tokens: int
    model_used: str
    user_id: int | None = None
    variant: ABTestVariant | None = None


@dataclass(slots=True)
class ABTestResult:
    """نتيجة تراكمية لاختبار A/B حسب المتغير."""

    variant: ABTestVariant
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    user_satisfaction: float = 0.0
    conversion_rate: float = 0.0
