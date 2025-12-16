"""Test Open/Closed Principle - Verify extensibility without modification."""

from datetime import UTC, datetime, timedelta

import pytest

from app.analytics.application.anomaly_detection import StatisticalAnomalyDetector
from app.analytics.application.custom_report_generators import (
    PerformanceReportGenerator,
    SecurityReportGenerator,
)
from app.analytics.application.ml_anomaly_detection import (
    CompositeAnomalyDetector,
    MLBasedAnomalyDetector,
)
from app.analytics.domain.entities import UsageMetric
from app.analytics.domain.value_objects import MetricType
from app.analytics.infrastructure.in_memory_repository import InMemoryMetricsRepository


class TestOCPAnomalyDetection:
    """Test that we can add new detectors without modifying existing code."""

    def test_ml_detector_can_be_used(self):
        """Test ML detector works with same interface."""
        detector = MLBasedAnomalyDetector()
        metrics = [
            UsageMetric(
                timestamp=datetime.now(UTC),
                metric_type=MetricType.COUNTER,
                name="api_request",
                value=1.0,
                status_code=200,
            )
        ]

        anomalies = detector.detect(metrics)
        assert isinstance(anomalies, list)

    def test_composite_detector_combines_multiple(self):
        """Test composite detector combines results from multiple detectors."""
        statistical = StatisticalAnomalyDetector()
        ml_based = MLBasedAnomalyDetector()
        composite = CompositeAnomalyDetector([statistical, ml_based])

        now = datetime.now(UTC)
        metrics = []
        for i in range(24):
            count = 100 if i < 23 else 500
            for _ in range(count):
                metrics.append(
                    UsageMetric(
                        timestamp=now - timedelta(hours=23 - i),
                        metric_type=MetricType.COUNTER,
                        name="api_request",
                        value=1.0,
                        status_code=200,
                    )
                )

        anomalies = composite.detect(metrics)
        assert isinstance(anomalies, list)

    def test_can_inject_different_detector_into_facade(self):
        """Test that we can inject different detectors into facade."""
        from app.analytics.api.analytics_facade import AnalyticsFacade
        from app.analytics.application.behavior_analysis import UserBehaviorAnalyzer
        from app.analytics.application.report_generation import UsageReportGenerator

        repo = InMemoryMetricsRepository()

        ml_detector = MLBasedAnomalyDetector()
        report_gen = UsageReportGenerator(repo)
        behavior_analyzer = UserBehaviorAnalyzer(repo)

        facade = AnalyticsFacade(
            repository=repo, anomaly_detector=ml_detector, report_generator=report_gen, behavior_analyzer=behavior_analyzer
        )

        assert facade.anomaly_detector is ml_detector


class TestOCPReportGeneration:
    """Test that we can add new report generators without modifying existing code."""

    def test_security_report_generator(self):
        """Test security report generator works."""
        repo = InMemoryMetricsRepository()
        generator = SecurityReportGenerator(repo)

        now = datetime.now(UTC)
        start = now - timedelta(hours=1)

        for i in range(50):
            status = 401 if i < 5 else 200
            repo.save(
                UsageMetric(
                    timestamp=now - timedelta(minutes=i),
                    metric_type=MetricType.COUNTER,
                    name="api_request",
                    value=1.0,
                    status_code=status,
                    user_id=f"user{i % 10}",
                )
            )

        report = generator.generate({"start_time": start, "end_time": now})

        assert "security_summary" in report
        assert "authentication_failures" in report
        assert report["security_summary"]["total_requests"] == 50

    def test_performance_report_generator(self):
        """Test performance report generator works."""
        repo = InMemoryMetricsRepository()
        generator = PerformanceReportGenerator(repo)

        now = datetime.now(UTC)
        start = now - timedelta(hours=1)

        for i in range(50):
            repo.save(
                UsageMetric(
                    timestamp=now - timedelta(minutes=i),
                    metric_type=MetricType.GAUGE,
                    name="response_time",
                    value=float(100 + i * 10),
                    endpoint=f"/api/endpoint{i % 5}",
                )
            )

        report = generator.generate({"start_time": start, "end_time": now})

        assert "performance_summary" in report
        assert "slow_endpoints" in report

    def test_can_inject_different_generator_into_facade(self):
        """Test that we can inject different generators into facade."""
        from app.analytics.api.analytics_facade import AnalyticsFacade
        from app.analytics.application.anomaly_detection import StatisticalAnomalyDetector
        from app.analytics.application.behavior_analysis import UserBehaviorAnalyzer

        repo = InMemoryMetricsRepository()

        detector = StatisticalAnomalyDetector()
        security_gen = SecurityReportGenerator(repo)
        behavior_analyzer = UserBehaviorAnalyzer(repo)

        facade = AnalyticsFacade(
            repository=repo, anomaly_detector=detector, report_generator=security_gen, behavior_analyzer=behavior_analyzer
        )

        assert facade.report_generator is security_gen


class TestExtensibilityWithoutModification:
    """Verify that adding new features doesn't require modifying existing code."""

    def test_no_modification_needed_for_new_detector(self):
        """Verify MLBasedAnomalyDetector doesn't modify existing code."""
        import inspect

        from app.analytics.application.anomaly_detection import StatisticalAnomalyDetector

        stat_source = inspect.getsource(StatisticalAnomalyDetector)

        assert "MLBasedAnomalyDetector" not in stat_source
        assert "ml_anomaly_detection" not in stat_source

    def test_no_modification_needed_for_new_generator(self):
        """Verify SecurityReportGenerator doesn't modify existing code."""
        import inspect

        from app.analytics.application.report_generation import UsageReportGenerator

        usage_source = inspect.getsource(UsageReportGenerator)

        assert "SecurityReportGenerator" not in usage_source
        assert "custom_report_generators" not in usage_source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
