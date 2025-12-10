"""ML-based anomaly detection - Demonstrates Open/Closed Principle.

This module can be added WITHOUT modifying existing code.
"""

from typing import Any

from app.analytics.domain.entities import Anomaly, UsageMetric
from app.analytics.domain.interfaces import AnomalyDetector


class MLBasedAnomalyDetector(AnomalyDetector):
    """
    ML-based anomaly detector - OCP in action.

    This class can be added to the system without modifying:
    - AnomalyDetector interface
    - StatisticalAnomalyDetector
    - AnalyticsFacade
    - Any other existing code

    Simply inject this instead of StatisticalAnomalyDetector.
    """

    def __init__(self, model_config: dict[str, Any] | None = None):
        self.model_config = model_config or {}
        self.model = self._load_model()

    def detect(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Detect anomalies using ML model."""
        if not metrics:
            return []

        features = self._extract_features(metrics)
        predictions = self._predict_anomalies(features)

        return self._convert_to_anomalies(predictions, metrics)

    def _load_model(self) -> Any:
        """Load ML model - placeholder for actual implementation."""
        return None

    def _extract_features(self, metrics: list[UsageMetric]) -> list[dict[str, float]]:
        """Extract features for ML model."""
        return [
            {
                "request_count": 1.0,
                "error_rate": 1.0 if (m.status_code and m.status_code >= 400) else 0.0,
                "hour_of_day": float(m.timestamp.hour),
            }
            for m in metrics
        ]

    def _predict_anomalies(self, features: list[dict[str, float]]) -> list[bool]:
        """Predict anomalies using ML model."""
        return [False] * len(features)

    def _convert_to_anomalies(self, predictions: list[bool], metrics: list[UsageMetric]) -> list[Anomaly]:
        """Convert predictions to Anomaly objects."""
        from datetime import UTC, datetime

        anomalies = []
        for i, is_anomaly in enumerate(predictions):
            if is_anomaly and i < len(metrics):
                anomalies.append(
                    Anomaly(
                        type="ml_detected_anomaly",
                        timestamp=metrics[i].timestamp,
                        severity="medium",
                        details={"metric_index": i},
                        description="Anomaly detected by ML model",
                    )
                )
        return anomalies


class CompositeAnomalyDetector(AnomalyDetector):
    """
    Composite detector - Combines multiple detectors.

    Another example of OCP: We can combine detectors without modifying them.
    """

    def __init__(self, detectors: list[AnomalyDetector]):
        self.detectors = detectors

    def detect(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Run all detectors and combine results."""
        all_anomalies = []
        for detector in self.detectors:
            anomalies = detector.detect(metrics)
            all_anomalies.extend(anomalies)

        return self._deduplicate(all_anomalies)

    def _deduplicate(self, anomalies: list[Anomaly]) -> list[Anomaly]:
        """Remove duplicate anomalies."""
        seen = set()
        unique = []

        for anomaly in anomalies:
            key = (anomaly.type, anomaly.timestamp.isoformat(), anomaly.severity)
            if key not in seen:
                seen.add(key)
                unique.append(anomaly)

        return unique
