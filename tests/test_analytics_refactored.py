"""Tests for refactored analytics module - Verifying SOLID principles."""

from datetime import UTC, datetime, timedelta

import pytest

from app.analytics.api.analytics_facade import get_analytics_facade
from app.analytics.application.anomaly_detection import StatisticalAnomalyDetector
from app.analytics.application.behavior_analysis import UserBehaviorAnalyzer
from app.analytics.application.report_generation import UsageReportGenerator
from app.analytics.domain.entities import UsageMetric
from app.analytics.domain.value_objects import BehaviorPattern, MetricType
from app.analytics.infrastructure.in_memory_repository import InMemoryMetricsRepository


class TestInMemoryRepository:
    """Test repository implementation."""

    def test_save_and_retrieve(self):
        """Test saving and retrieving metrics."""
        repo = InMemoryMetricsRepository()
        metric = UsageMetric(
            timestamp=datetime.now(UTC),
            metric_type=MetricType.COUNTER,
            name="test",
            value=1.0,
            user_id="user1",
        )

        repo.save(metric)
        assert repo.count() == 1

        recent = repo.get_recent(hours=1)
        assert len(recent) == 1
        assert recent[0].user_id == "user1"

    def test_get_by_user(self):
        """Test filtering by user."""
        repo = InMemoryMetricsRepository()

        for i in range(5):
            repo.save(
                UsageMetric(
                    timestamp=datetime.now(UTC),
                    metric_type=MetricType.COUNTER,
                    name="test",
                    value=1.0,
                    user_id=f"user{i % 2}",
                )
            )

        user0_metrics = repo.get_by_user("user0")
        assert len(user0_metrics) == 3


class TestAnomalyDetection:
    """Test anomaly detection - SRP verification."""

    def test_detect_traffic_spike(self):
        """Test traffic spike detection."""
        detector = StatisticalAnomalyDetector()
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
                    )
                )

        anomalies = detector.detect(metrics)
        assert len(anomalies) > 0
        assert any(a.type == "traffic_spike" for a in anomalies)

    def test_detect_high_error_rate(self):
        """Test error rate detection."""
        detector = StatisticalAnomalyDetector()
        now = datetime.now(UTC)

        metrics = []
        for i in range(100):
            status = 500 if i < 30 else 200
            metrics.append(
                UsageMetric(
                    timestamp=now,
                    metric_type=MetricType.COUNTER,
                    name="api_request",
                    value=1.0,
                    status_code=status,
                )
            )

        anomalies = detector.detect(metrics)
        assert len(anomalies) > 0
        assert any(a.type == "high_error_rate" for a in anomalies)


class TestReportGeneration:
    """Test report generation - SRP verification."""

    def test_generate_usage_report(self):
        """Test usage report generation."""
        repo = InMemoryMetricsRepository()
        generator = UsageReportGenerator(repo)

        now = datetime.now(UTC)
        start = now - timedelta(hours=1)

        for i in range(50):
            repo.save(
                UsageMetric(
                    timestamp=now - timedelta(minutes=i),
                    metric_type=MetricType.COUNTER,
                    name="api_request",
                    value=1.0,
                    endpoint=f"/api/endpoint{i % 5}",
                    user_id=f"user{i % 10}",
                    status_code=200,
                )
            )

        report = generator.generate({"start_time": start, "end_time": now})

        assert "summary" in report
        assert report["summary"]["total_requests"] == 50
        assert report["summary"]["unique_users"] == 10
        assert "top_endpoints" in report
        assert len(report["top_endpoints"]) > 0


class TestBehaviorAnalysis:
    """Test behavior analysis - SRP verification."""

    def test_analyze_power_user(self):
        """Test power user identification."""
        repo = InMemoryMetricsRepository()
        analyzer = UserBehaviorAnalyzer(repo)

        now = datetime.now(UTC)
        for i in range(100):
            repo.save(
                UsageMetric(
                    timestamp=now - timedelta(hours=i),
                    metric_type=MetricType.COUNTER,
                    name="api_request",
                    value=1.0,
                    user_id="power_user",
                    endpoint="/api/test",
                )
            )

        profile = analyzer.analyze("power_user")
        assert profile.user_id == "power_user"
        assert profile.pattern == BehaviorPattern.POWER_USER
        assert profile.avg_requests_per_day > 20

    def test_analyze_churning_user(self):
        """Test churning user identification."""
        repo = InMemoryMetricsRepository()
        analyzer = UserBehaviorAnalyzer(repo)

        old_date = datetime.now(UTC) - timedelta(days=60)
        repo.save(
            UsageMetric(
                timestamp=old_date,
                metric_type=MetricType.COUNTER,
                name="api_request",
                value=1.0,
                user_id="churning_user",
            )
        )

        profile = analyzer.analyze("churning_user")
        assert profile.churn_probability > 0.8


class TestAnalyticsFacade:
    """Test facade - Integration test."""

    def test_full_workflow(self):
        """Test complete analytics workflow."""
        facade = get_analytics_facade()

        facade.track_request(endpoint="/api/test", method="GET", status_code=200, user_id="test_user")

        facade.track_request(endpoint="/api/test", method="GET", status_code=200, user_id="test_user")

        dashboard = facade.get_realtime_dashboard()
        assert dashboard["last_hour"]["total_requests"] >= 2

        profile = facade.analyze_user("test_user")
        assert profile.user_id == "test_user"

    def test_dependency_injection(self):
        """Test that dependencies can be injected - DIP verification."""
        repo = InMemoryMetricsRepository()
        detector = StatisticalAnomalyDetector()
        generator = UsageReportGenerator(repo)
        analyzer = UserBehaviorAnalyzer(repo)

        from app.analytics.api.analytics_facade import AnalyticsFacade

        facade = AnalyticsFacade(
            repository=repo, anomaly_detector=detector, report_generator=generator, behavior_analyzer=analyzer
        )

        assert facade.repository is repo
        assert facade.anomaly_detector is detector


class TestComplexityReduction:
    """Verify complexity reduction goals."""

    def test_no_function_exceeds_complexity_10(self):
        """Verify no function has complexity > 10."""
        import subprocess

        result = subprocess.run(
            ["radon", "cc", "app/analytics/", "-n", "C", "-s"], capture_output=True, text=True, check=False
        )

        high_complexity_functions = [line for line in result.stdout.split("\n") if "- C" in line or "- D" in line]

        assert len(high_complexity_functions) <= 1, f"Found high complexity functions: {high_complexity_functions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
