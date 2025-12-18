"""Anomaly detection use case - Single Responsibility Principle."""

import statistics
from collections import defaultdict
from datetime import UTC, datetime

from .entities import Anomaly, UsageMetric
from .interfaces import AnomalyDetector


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detector - SRP: Only detects anomalies."""

    def detect(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        anomalies.extend(self._detect_traffic_spikes(metrics))
        anomalies.extend(self._detect_error_rate_anomalies(metrics))
        return anomalies

    def _detect_traffic_spikes(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Detect traffic spikes - Complexity < 10."""
        anomalies = []
        hourly_counts = self._group_by_hour(metrics)

        if len(hourly_counts) < 3:
            return anomalies

        counts = list(hourly_counts.values())
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 0

        if stdev == 0:
            return anomalies

        for hour, count in hourly_counts.items():
            if count > mean + (2 * stdev):
                severity = "high" if count > mean + (3 * stdev) else "medium"
                hour_timestamp = datetime.strptime(hour, "%Y-%m-%d-%H").replace(tzinfo=UTC)
                anomalies.append(
                    Anomaly(
                        type="traffic_spike",
                        timestamp=hour_timestamp,
                        severity=severity,
                        details={"hour": hour, "count": count, "expected": round(mean)},
                        description=f"Traffic spike detected: {count} requests (expected: {round(mean)})",
                    )
                )

        return anomalies

    def _detect_error_rate_anomalies(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Detect high error rates - Complexity < 10."""
        anomalies = []
        hourly_counts = self._group_by_hour(metrics)

        for hour in hourly_counts.keys():
            hour_metrics = [m for m in metrics if self._get_hour_key(m.timestamp) == hour and m.name == "api_request"]

            if not hour_metrics:
                continue

            errors = sum(1 for m in hour_metrics if m.status_code and m.status_code >= 400)
            error_rate = (errors / len(hour_metrics) * 100) if hour_metrics else 0

            if error_rate > 10:
                severity = "critical" if error_rate > 20 else "high"
                hour_timestamp = datetime.strptime(hour, "%Y-%m-%d-%H").replace(tzinfo=UTC)
                anomalies.append(
                    Anomaly(
                        type="high_error_rate",
                        timestamp=hour_timestamp,
                        severity=severity,
                        details={"hour": hour, "error_rate": round(error_rate, 2)},
                        description=f"High error rate: {round(error_rate, 2)}%",
                    )
                )

        return anomalies

    def _group_by_hour(self, metrics: list[UsageMetric]) -> dict[str, int]:
        """Group metrics by hour."""
        hourly_counts: dict[str, int] = defaultdict(int)
        for m in metrics:
            if m.name == "api_request":
                hour_key = self._get_hour_key(m.timestamp)
                hourly_counts[hour_key] += 1
        return hourly_counts

    def _get_hour_key(self, timestamp: datetime) -> str:
        """Get hour key from timestamp."""
        return timestamp.strftime("%Y-%m-%d-%H")
