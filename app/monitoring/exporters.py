"""
مصدرو المقاييس (Metrics Exporters).

يوفر مصدري مقاييس لتنسيقات مختلفة (JSON, InfluxDB, Prometheus).
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from app.monitoring.metrics import MetricsCollector
from app.monitoring.metrics import PrometheusExporter as BasePrometheusExporter

logger = logging.getLogger(__name__)


class MetricExporter(ABC):
    """
    واجهة مصدر المقاييس الأساسية.
    """

    def __init__(self, collector: MetricsCollector) -> None:
        """
        تهيئة المصدر.

        Args:
            collector: جامع المقاييس
        """
        self.collector = collector

    @abstractmethod
    def export(self) -> Any:
        """
        يصدر المقاييس.

        Returns:
            Any: المقاييس المصدرة
        """
        pass


class JSONExporter(MetricExporter):
    """
    مصدر مقاييس JSON.
    """

    def export(self) -> dict[str, Any]:
        """
        يصدر المقاييس بتنسيق JSON.

        Returns:
            dict[str, Any]: المقاييس
        """
        return self.collector.get_all_metrics()

    def export_to_file(self, filepath: str) -> None:
        """
        يصدر المقاييس إلى ملف JSON.

        Args:
            filepath: مسار الملف
        """
        data = self.export()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"✅ Metrics exported to {filepath}")


class InfluxDBExporter(MetricExporter):
    """
    مصدر مقاييس InfluxDB (Line Protocol).
    """

    def export(self) -> str:
        """
        يصدر المقاييس بتنسيق InfluxDB Line Protocol.

        Returns:
            str: المقاييس
        """
        lines = []
        timestamp_ns = int(time.time() * 1e9)

        metrics = self.collector.get_all_metrics()

        # Counters
        for name, value in metrics["counters"].items():
            parsed = self._parse_key(name)
            tags_str = self._format_tags(parsed["labels"])
            if tags_str:
                lines.append(f"{parsed['name']},{tags_str} value={value} {timestamp_ns}")
            else:
                lines.append(f"{parsed['name']} value={value} {timestamp_ns}")

        # Gauges
        for name, value in metrics["gauges"].items():
            parsed = self._parse_key(name)
            tags_str = self._format_tags(parsed["labels"])
            if tags_str:
                lines.append(f"{parsed['name']},{tags_str} value={value} {timestamp_ns}")
            else:
                lines.append(f"{parsed['name']} value={value} {timestamp_ns}")

        # Histograms (stats)
        for name, stats in metrics["histograms"].items():
            parsed = self._parse_key(name)
            tags_str = self._format_tags(parsed["labels"])

            field_set = []
            for k, v in stats.items():
                field_set.append(f"{k}={v}")
            fields_str = ",".join(field_set)

            if tags_str:
                lines.append(f"{parsed['name']},{tags_str} {fields_str} {timestamp_ns}")
            else:
                lines.append(f"{parsed['name']} {fields_str} {timestamp_ns}")

        return "\n".join(lines)

    def _parse_key(self, key: str) -> dict[str, Any]:
        """
        يحلل مفتاح المقياس لاستخراج الاسم والتسميات.
        """
        if "{" not in key:
            return {"name": key, "labels": {}}

        name_part, labels_part = key.split("{", 1)
        labels_part = labels_part.rstrip("}")

        labels = {}
        if labels_part:
            for item in labels_part.split(","):
                k, v = item.split("=", 1)
                labels[k] = v.strip('"')

        return {"name": name_part, "labels": labels}

    def _format_tags(self, labels: dict[str, str]) -> str:
        """
        ينسق التسميات كـ InfluxDB tags.
        """
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class PrometheusExporter(BasePrometheusExporter, MetricExporter):
    """
    مصدر مقاييس Prometheus (محسن).
    """

    def export(self) -> str:
        """
        يصدر المقاييس بتنسيق Prometheus.

        Returns:
            str: المقاييس
        """
        return self.export_text()
