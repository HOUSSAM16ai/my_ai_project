from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.aiops_self_healing_service import (
    AIOpsService,
    AnomalySeverity,
    AnomalyType,
    HealingAction,
    MetricType,
    TelemetryData,
    get_aiops_service,
)


class TestAIOpsService:
    @pytest.fixture
    def aiops_service(self):
        # Create a fresh instance for each test to avoid state leakage
        service = AIOpsService()
        return service

    def test_singleton_instance(self):
        s1 = get_aiops_service()
        s2 = get_aiops_service()
        assert s1 is s2

    def test_collect_telemetry_updates_baseline(self, aiops_service):
        service_name = "test-service"
        metric_type = MetricType.LATENCY

        # Ingest enough data to trigger baseline calculation (need >= 10 points)
        for i in range(15):
            data = TelemetryData(
                metric_id=f"m-{i}",
                service_name=service_name,
                metric_type=metric_type,
                value=100.0 + (i % 2),  # Alternating 100, 101
                timestamp=datetime.now(UTC),
            )
            aiops_service.collect_telemetry(data)

        key = f"{service_name}:{metric_type.value}"
        baseline = aiops_service.baseline_metrics.get(key)

        assert baseline is not None
        assert baseline["mean"] == pytest.approx(100.5, abs=1.0)
        assert baseline["median"] in [100.0, 101.0]

    def test_detect_zscore_anomaly_latency(self, aiops_service):
        service_name = "latency-service"
        metric_type = MetricType.LATENCY

        # Establish stable baseline (mean=100, stdev=0)
        # Actually need stdev > 0 for zscore.
        # Let's add some variance.
        values = [100.0, 102.0] * 10
        for i, v in enumerate(values):
            data = TelemetryData(
                metric_id=f"m-{i}",
                service_name=service_name,
                metric_type=metric_type,
                value=v,
                timestamp=datetime.now(UTC),
            )
            aiops_service.collect_telemetry(data)

        # Verify baseline exists and stdev > 0
        key = f"{service_name}:{metric_type.value}"
        assert aiops_service.baseline_metrics[key]["stdev"] > 0

        # Inject anomaly (spike)
        # Mean ~101, stdev ~1.
        # Value 120 should be >> 3 sigma
        anomaly_data = TelemetryData(
            metric_id="anomaly-1",
            service_name=service_name,
            metric_type=metric_type,
            value=120.0,
            timestamp=datetime.now(UTC),
        )

        with patch.object(aiops_service, "_trigger_healing") as mock_healing:
            aiops_service.collect_telemetry(anomaly_data)

            # Check if anomaly was recorded
            assert len(aiops_service.anomalies) == 1
            anomaly = next(iter(aiops_service.anomalies.values()))
            assert anomaly.anomaly_type == AnomalyType.LATENCY_SPIKE
            assert anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]

            mock_healing.assert_called_once()

    def test_detect_error_rate_threshold_anomaly(self, aiops_service):
        service_name = "error-service"
        metric_type = MetricType.ERROR_RATE

        # Seed data to establish baseline (required by implementation)
        for i in range(10):
            data = TelemetryData(
                metric_id=f"seed-{i}",
                service_name=service_name,
                metric_type=metric_type,
                value=0.01,  # Low error rate
                timestamp=datetime.now(UTC),
            )
            aiops_service.collect_telemetry(data)

        # Error rate > 0.05 triggers anomaly
        data = TelemetryData(
            metric_id="err-1",
            service_name=service_name,
            metric_type=metric_type,
            value=0.06,
            timestamp=datetime.now(UTC),
        )

        with patch.object(aiops_service, "_trigger_healing") as mock_healing:
            aiops_service.collect_telemetry(data)

            assert len(aiops_service.anomalies) == 1
            anomaly = next(iter(aiops_service.anomalies.values()))
            assert anomaly.anomaly_type == AnomalyType.ERROR_RATE_INCREASE
            assert anomaly.metric_value == 0.06

            mock_healing.assert_called_once()

    def test_healing_action_determination(self, aiops_service):
        # 1. Latency Spike -> Scale Up
        anomaly_latency = MagicMock(
            anomaly_type=AnomalyType.LATENCY_SPIKE, service_name="svc-1", anomaly_id="a1"
        )
        action_latency = aiops_service._determine_healing_action(anomaly_latency)
        assert action_latency["action"] == HealingAction.SCALE_UP

        # 2. Error Rate -> Circuit Breaker
        anomaly_error = MagicMock(
            anomaly_type=AnomalyType.ERROR_RATE_INCREASE, service_name="svc-1", anomaly_id="a2"
        )
        action_error = aiops_service._determine_healing_action(anomaly_error)
        assert action_error["action"] == HealingAction.ENABLE_CIRCUIT_BREAKER

        # 3. Traffic Anomaly (High) -> Scale Up
        anomaly_traffic = MagicMock(
            anomaly_type=AnomalyType.TRAFFIC_ANOMALY,
            metric_value=200,
            expected_value=100,
            service_name="svc-1",
            anomaly_id="a3",
        )
        action_traffic = aiops_service._determine_healing_action(anomaly_traffic)
        assert action_traffic["action"] == HealingAction.SCALE_UP

        # 4. Unknown/Low Traffic -> None
        anomaly_low = MagicMock(
            anomaly_type=AnomalyType.TRAFFIC_ANOMALY,
            metric_value=50,
            expected_value=100,  # Lower than expected, maybe not scale up
            service_name="svc-1",
            anomaly_id="a4",
        )
        # The logic is: metric_value > expected_value
        action_low = aiops_service._determine_healing_action(anomaly_low)
        assert action_low is None

    def test_execute_healing(self, aiops_service):
        # Create an anomaly first
        anomaly_id = "test-anomaly-id"
        service_name = "healing-service"

        # Manually inject anomaly into state
        from app.services.aiops_self_healing_service import AnomalyDetection

        anomaly = AnomalyDetection(
            anomaly_id=anomaly_id,
            service_name=service_name,
            anomaly_type=AnomalyType.LATENCY_SPIKE,
            severity=AnomalySeverity.HIGH,
            detected_at=datetime.now(UTC),
            metric_value=200,
            expected_value=100,
            confidence=1.0,
            description="test",
        )
        aiops_service.anomalies[anomaly_id] = anomaly

        # Trigger healing via public method to cover flow
        with patch("uuid.uuid4", return_value="decision-id"):
            aiops_service._trigger_healing(anomaly)

        assert "decision-id" in aiops_service.healing_decisions
        decision = aiops_service.healing_decisions["decision-id"]
        assert decision.success is True
        assert anomaly.resolved is True
        assert anomaly.resolved_at is not None

    def test_forecast_load(self, aiops_service):
        service_name = "forecast-svc"
        metric_type = MetricType.REQUEST_RATE

        # Need at least 100 points
        base_time = datetime.now(UTC) - timedelta(days=7)
        for i in range(120):
            # Create a linear trend: y = x
            data = TelemetryData(
                metric_id=f"m-{i}",
                service_name=service_name,
                metric_type=metric_type,
                value=float(i),
                timestamp=base_time + timedelta(hours=i),
            )
            aiops_service.collect_telemetry(data)

        forecast = aiops_service.forecast_load(service_name, metric_type, hours_ahead=10)

        assert forecast is not None
        assert forecast.service_name == service_name
        # Last value was 119. Trend is +1 per step.
        # Forecast 10 steps ahead should be approx 129.
        # The logic uses last 168 points. We have 120.
        # It calculates linear regression on indices 0..N

        # Let's just check it returns a valid forecast object
        assert forecast.predicted_load > 119
        assert len(aiops_service.forecasts[service_name]) == 1

    def test_forecast_load_insufficient_data(self, aiops_service):
        forecast = aiops_service.forecast_load("new-svc", MetricType.REQUEST_RATE)
        assert forecast is None

    def test_calculate_trend(self, aiops_service):
        # y = 2x + 1
        values = [1.0, 3.0, 5.0, 7.0, 9.0]
        trend = aiops_service._calculate_trend(values)
        assert trend == pytest.approx(2.0)

        # Constant
        values = [5.0, 5.0, 5.0]
        trend = aiops_service._calculate_trend(values)
        assert trend == 0.0

    def test_generate_capacity_plan(self, aiops_service):
        service_name = "cap-svc"

        # Seed data for forecasting
        for i in range(110):
            data = TelemetryData(
                metric_id=f"id-{i}",
                service_name=service_name,
                metric_type=MetricType.REQUEST_RATE,
                value=100.0,
                timestamp=datetime.now(UTC),
            )
            aiops_service.collect_telemetry(data)

        plan = aiops_service.generate_capacity_plan(service_name)

        assert plan is not None
        assert plan.service_name == service_name
        assert plan.recommended_capacity > plan.expected_peak_load
        assert service_name in aiops_service.capacity_plans

    def test_root_cause_analysis(self, aiops_service):
        service_name = "rca-svc"
        anomaly_id = "anom-1"

        # Create anomaly
        from app.services.aiops_self_healing_service import AnomalyDetection

        anomaly = AnomalyDetection(
            anomaly_id=anomaly_id,
            service_name=service_name,
            anomaly_type=AnomalyType.LATENCY_SPIKE,
            severity=AnomalySeverity.HIGH,
            detected_at=datetime.now(UTC),
            metric_value=500,
            expected_value=100,
            confidence=0.9,
            description="Latency high",
        )
        aiops_service.anomalies[anomaly_id] = anomaly

        # 1. Test "Correlated with increased error rate"
        # Add error rate metrics
        aiops_service.collect_telemetry(
            TelemetryData(
                metric_id="err-1",
                service_name=service_name,
                metric_type=MetricType.ERROR_RATE,
                value=0.15,
                timestamp=datetime.now(UTC),
            )
        )

        causes = aiops_service.analyze_root_cause(anomaly_id)
        assert "Correlated with increased error rate" in causes

        # 2. Test CPU Usage
        aiops_service.collect_telemetry(
            TelemetryData(
                metric_id="cpu-1",
                service_name=service_name,
                metric_type=MetricType.CPU_USAGE,
                value=85.0,
                timestamp=datetime.now(UTC),
            )
        )

        causes = aiops_service.analyze_root_cause(anomaly_id)
        assert "High CPU usage detected" in causes

    def test_get_aiops_metrics_and_health(self, aiops_service):
        # Simply call them to ensure no crashes and basic structure
        metrics = aiops_service.get_aiops_metrics()
        assert "total_anomalies" in metrics
        assert "resolution_rate" in metrics

        health = aiops_service.get_service_health("non-existent")
        assert health["health_status"] == "healthy"  # No anomalies = healthy

    def test_percentile_calculation(self, aiops_service):
        values = list(range(100))  # 0..99
        p95 = aiops_service._percentile(values, 95)
        assert p95 == 95

        p99 = aiops_service._percentile(values, 99)
        assert p99 == 99
