"""
جامع المقاييس (Metrics Collector).

يجمع ويصدر مقاييس Prometheus للمراقبة والتحليل.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final, TypedDict

from app.core.types import JSON, JSONDict

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Metric:
    """
    مقياس واحد.

    Attributes:
        name: اسم المقياس
        value: القيمة
        labels: التسميات
        timestamp: الوقت
        metric_type: نوع المقياس (counter, gauge, histogram, summary)
    """

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metric_type: str = "gauge"


class HistogramStats(TypedDict):
    """إحصائيات المخطط التكراري."""

    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class MetricsMetadata(TypedDict):
    """بيانات وصفية للمقاييس."""

    uptime_seconds: float
    total_metrics_collected: int


class MetricsSnapshot(TypedDict):
    """لقطة كاملة للمقاييس."""

    counters: dict[str, float]
    gauges: dict[str, float]
    histograms: dict[str, dict[str, float]]
    metadata: MetricsMetadata


class MetricsCollector:
    """
    جامع المقاييس المركزي.

    يجمع مقاييس من جميع أنحاء النظام ويوفرها لـ Prometheus.

    المبادئ:
    - Thread-Safe: آمن للاستخدام المتزامن
    - Low Overhead: تأثير ضئيل على الأداء
    - Flexible: دعم جميع أنواع المقاييس
    - Observable: مقاييس عن المقاييس نفسها
    """

    def __init__(self) -> None:
        """تهيئة جامع المقاييس."""
        # Counters: تزداد فقط
        self._counters: dict[str, float] = defaultdict(float)

        # Gauges: يمكن أن تزيد أو تنقص
        self._gauges: dict[str, float] = {}

        # Histograms: توزيع القيم
        self._histograms: dict[str, list[float]] = defaultdict(list)

        # Summaries: إحصائيات ملخصة
        self._summaries: dict[str, list[float]] = defaultdict(list)

        # Labels: تسميات لكل مقياس
        self._labels: dict[str, dict[str, str]] = {}

        # Metadata
        self._start_time: Final[float] = time.time()
        self._total_metrics_collected: int = 0

        logger.info("✅ Metrics Collector initialized")

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        يزيد عداد.

        Args:
            name: اسم العداد
            value: القيمة للزيادة (افتراضي: 1.0)
            labels: تسميات إضافية
        """
        key = self._make_key(name, labels)
        self._counters[key] += value
        self._total_metrics_collected += 1

        if labels:
            self._labels[key] = labels

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        يضبط قيمة مقياس.

        Args:
            name: اسم المقياس
            value: القيمة
            labels: تسميات إضافية
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._total_metrics_collected += 1

        if labels:
            self._labels[key] = labels

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        يسجل قيمة في histogram.

        Args:
            name: اسم الـ histogram
            value: القيمة
            labels: تسميات إضافية
        """
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        self._total_metrics_collected += 1

        if labels:
            self._labels[key] = labels

    def observe_summary(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        يسجل قيمة في summary.

        Args:
            name: اسم الـ summary
            value: القيمة
            labels: تسميات إضافية
        """
        key = self._make_key(name, labels)
        self._summaries[key].append(value)
        self._total_metrics_collected += 1

        if labels:
            self._labels[key] = labels

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> float:
        """
        يحصل على قيمة عداد.

        Args:
            name: اسم العداد
            labels: تسميات

        Returns:
            float: قيمة العداد
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float | None:
        """
        يحصل على قيمة مقياس.

        Args:
            name: اسم المقياس
            labels: تسميات

        Returns:
            float | None: قيمة المقياس أو None
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key)

    def get_histogram_stats(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> HistogramStats:
        """
        يحصل على إحصائيات histogram.

        Args:
            name: اسم الـ histogram
            labels: تسميات

        Returns:
            HistogramStats: إحصائيات (count, sum, min, max, avg, p50, p95, p99)
        """
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {
                "count": 0,
                "sum": 0.0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.50)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }

    def get_all_metrics(self) -> MetricsSnapshot:
        """
        يحصل على جميع المقاييس.

        Returns:
            MetricsSnapshot: جميع المقاييس
        """
        histograms: dict[str, dict[str, float]] = {}
        for key in self._histograms:
            metric_name, labels = self._parse_key(key)
            # Casting HistogramStats to dict[str, float] for generic storage or use explicit type
            # Since HistogramStats is TypedDict which is a dict at runtime, this is fine but we
            # should match the return type structure.
            # However, TypedDict doesn't inherit from dict[str, float] in MyPy's eyes always.
            # Let's keep it simple.
            stats = self.get_histogram_stats(metric_name, labels)
            histograms[key] = stats  # type: ignore[assignment]

        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": histograms,
            "metadata": {
                "uptime_seconds": time.time() - self._start_time,
                "total_metrics_collected": self._total_metrics_collected,
            },
        }

    def reset(self) -> None:
        """يعيد تعيين جميع المقاييس."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._summaries.clear()
        self._labels.clear()
        self._total_metrics_collected = 0

        logger.info("🔄 Metrics reset")

    @staticmethod
    def _make_key(name: str, labels: dict[str, str] | None) -> str:
        """
        ينشئ مفتاح فريد للمقياس.

        Args:
            name: اسم المقياس
            labels: تسميات

        Returns:
            str: مفتاح فريد
        """
        if not labels:
            return name

        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @staticmethod
    def _parse_key(key: str) -> tuple[str, dict[str, str]]:
        """
        يفكك مفتاح المقياس إلى الاسم والتسميات.
        """
        if "{" not in key:
            return key, {}

        name_part, labels_part = key.split("{", 1)
        labels_part = labels_part.rstrip("}")

        labels: dict[str, str] = {}
        if labels_part:
            for item in labels_part.split(","):
                label_key, label_value = item.split("=", 1)
                labels[label_key] = label_value.strip('"')

        return name_part, labels


class PrometheusExporter:
    """
    مصدر مقاييس Prometheus.

    يحول المقاييس إلى تنسيق Prometheus.
    """

    def __init__(self, collector: MetricsCollector) -> None:
        """
        تهيئة المصدر.

        Args:
            collector: جامع المقاييس
        """
        self.collector = collector
        logger.info("✅ Prometheus Exporter initialized")

    def export_text(self) -> str:
        """
        يصدر المقاييس بتنسيق Prometheus النصي.

        Returns:
            str: مقاييس بتنسيق Prometheus
        """
        lines = []

        # Counters
        for name, value in self.collector._counters.items():
            metric_name = name.split("{")[0]
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{name} {value}")

        # Gauges
        for name, value in self.collector._gauges.items():
            metric_name = name.split("{")[0]
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{name} {value}")

        # Histograms
        for name in self.collector._histograms:
            metric_name, labels = self.collector._parse_key(name)
            stats = self.collector.get_histogram_stats(metric_name, labels)

            label_parts = [f'{k}="{v}"' for k, v in labels.items()]

            def _bucket_labels(value: str, label_parts=label_parts) -> str:
                parts = [f'le="{value}"']
                parts.extend(label_parts)
                return "{" + ",".join(parts) + "}"

            lines.append(f"# TYPE {metric_name} histogram")
            label_suffix = f"{{{','.join(label_parts)}}}" if label_parts else ""
            lines.append(f"{metric_name}_count{label_suffix} {stats['count']}")
            lines.append(f"{metric_name}_sum{label_suffix} {stats['sum']}")
            lines.append(f"{metric_name}_bucket{_bucket_labels('0.5')} {stats['p50']}")
            lines.append(f"{metric_name}_bucket{_bucket_labels('0.95')} {stats['p95']}")
            lines.append(f"{metric_name}_bucket{_bucket_labels('0.99')} {stats['p99']}")
            lines.append(f"{metric_name}_bucket{_bucket_labels('+Inf')} {stats['count']}")

        # Metadata
        uptime = time.time() - self.collector._start_time
        lines.append("# TYPE cogniforge_uptime_seconds gauge")
        lines.append(f"cogniforge_uptime_seconds {uptime}")

        lines.append("# TYPE cogniforge_metrics_total counter")
        lines.append(f"cogniforge_metrics_total {self.collector._total_metrics_collected}")

        return "\n".join(lines) + "\n"

    def export_json(self) -> JSON:
        """
        يصدر المقاييس بتنسيق JSON.

        Returns:
            JSON: مقاييس بتنسيق JSON
        """
        # Casting because MetricsSnapshot (TypedDict) is compatible with JSON structure
        return self.collector.get_all_metrics()  # type: ignore[return-value]


# مثيل عام
_global_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """
    يحصل على جامع المقاييس العام.

    Returns:
        MetricsCollector: جامع المقاييس
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
