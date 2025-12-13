"""
Metrics Manager - Application Service
"""

import uuid

from ..domain.models import Metric, MetricType
from ..domain.ports import IMetricsCollector


class MetricsManager:
    """Manages metrics collection and retrieval"""

    def __init__(self, collector: IMetricsCollector):
        self._collector = collector

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
    ) -> Metric:
        """Record a new metric"""
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
        )
        self._collector.collect_metric(metric)
        return metric

    def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Retrieve metrics with optional filtering"""
        return self._collector.get_metrics(name=name, labels=labels, limit=limit)

    def get_metric_summary(self, name: str) -> dict[str, float]:
        """Get summary statistics for a metric"""
        metrics = self._collector.get_metrics(name=name, limit=1000)
        if not metrics:
            return {"count": 0, "sum": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
