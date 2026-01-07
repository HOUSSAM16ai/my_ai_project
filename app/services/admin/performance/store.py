"""مخزن مقاييس الأداء مع سياسات تصفية زمنية واضحة."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime

from app.services.admin.performance.metrics import PerformanceMetric


class MetricStore:
    """حاوية مسؤولة عن حفظ المقاييس وإرجاعها حسب نافذة زمنية."""

    def __init__(self, maxlen: int = 10_000) -> None:
        """يهيئ المخزن مع حد أقصى لعدد المقاييس المخزنة."""
        self.metrics: deque[PerformanceMetric] = deque(maxlen=maxlen)

    def append(self, metric: PerformanceMetric) -> None:
        """يضيف مقياسًا جديدًا إلى المخزن."""
        self.metrics.append(metric)

    def filter_by_time(
        self, category: str | None, hours: int
    ) -> list[PerformanceMetric]:
        """يعيد المقاييس الواقعة ضمن النافذة الزمنية المحددة."""
        cutoff_time = datetime.now(UTC).timestamp() - hours * 3600
        return [
            metric
            for metric in self.metrics
            if metric.timestamp.timestamp() > cutoff_time
            and (category is None or metric.category == category)
        ]
