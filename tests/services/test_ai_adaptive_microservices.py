from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.ai_engineering.ai_adaptive_microservices import (
    AIScalingEngine,
    IntelligentRouter,
    PredictiveHealthMonitor,
    ScalingDecision,
    ScalingDirection,
    SelfAdaptiveMicroservices,
    ServiceHealth,
    ServiceInstance,
    ServiceMetrics,
)

# --- Fixtures ---


@pytest.fixture
def scaling_engine():
    return AIScalingEngine()


@pytest.fixture
def intelligent_router():
    return IntelligentRouter()


@pytest.fixture
def health_monitor():
    return PredictiveHealthMonitor()


@pytest.fixture
def adaptive_system():
    return SelfAdaptiveMicroservices()


@pytest.fixture
def sample_metrics():
    return ServiceMetrics(
        service_name="test-service",
        timestamp=datetime.now(),
        cpu_usage=50.0,
        memory_usage=50.0,
        request_rate=100.0,
        error_rate=1.0,
        latency_p50=50.0,
        latency_p95=100.0,
        latency_p99=200.0,
        active_connections=100,
        queue_depth=10,
    )


@pytest.fixture
def high_load_metrics():
    return ServiceMetrics(
        service_name="test-service",
        timestamp=datetime.now(),
        cpu_usage=90.0,
        memory_usage=85.0,
        request_rate=500.0,
        error_rate=2.0,
        latency_p50=200.0,
        latency_p95=800.0,
        latency_p99=1500.0,
        active_connections=500,
        queue_depth=100,
    )


@pytest.fixture
def low_load_metrics():
    return ServiceMetrics(
        service_name="test-service",
        timestamp=datetime.now(),
        cpu_usage=10.0,
        memory_usage=20.0,
        request_rate=10.0,
        error_rate=0.0,
        latency_p50=10.0,
        latency_p95=20.0,
        latency_p99=30.0,
        active_connections=10,
        queue_depth=0,
    )


# --- AIScalingEngine Tests ---


class TestAIScalingEngine:
    def test_predict_load_insufficient_data(self, scaling_engine, sample_metrics):
        predicted_load, confidence = scaling_engine.predict_load("test-service", sample_metrics)
        assert predicted_load == sample_metrics.request_rate
        assert confidence == 0.3

    def test_predict_load_with_history(self, scaling_engine, sample_metrics):
        # Populate history
        history = []
        for i in range(20):
            metrics = ServiceMetrics(
                service_name="test-service",
                timestamp=datetime.now() - timedelta(minutes=20 - i),
                cpu_usage=50.0,
                memory_usage=50.0,
                request_rate=100.0 + (i * 2),  # Increasing trend
                error_rate=0.0,
                latency_p50=50.0,
                latency_p95=100.0,
                latency_p99=200.0,
                active_connections=100,
                queue_depth=10,
            )
            history.append(metrics)

        scaling_engine.historical_patterns["test-service"] = history

        predicted_load, confidence = scaling_engine.predict_load("test-service", sample_metrics)

        # Average load ~120, trend ~2 per min. 15 min window -> +30. Expected ~150
        assert predicted_load > 120
        # The variance of the linear trend 100, 102, ... is high enough that confidence hits the floor of 0.5
        assert confidence >= 0.5

    def test_calculate_optimal_instances_scale_up(self, scaling_engine, high_load_metrics):
        current_instances = 2
        decision = scaling_engine.calculate_optimal_instances(
            "test-service", high_load_metrics, current_instances
        )

        assert decision.direction == ScalingDirection.UP
        assert decision.target_instances > current_instances
        assert "High utilization" in decision.reason

    def test_calculate_optimal_instances_scale_down(self, scaling_engine, low_load_metrics):
        current_instances = 5
        decision = scaling_engine.calculate_optimal_instances(
            "test-service", low_load_metrics, current_instances
        )

        assert decision.direction == ScalingDirection.DOWN
        assert decision.target_instances < current_instances
        assert "Low utilization" in decision.reason

    def test_calculate_optimal_instances_stable(self, scaling_engine, sample_metrics):
        current_instances = 3
        # Adjust metrics to be in the sweet spot (60-70% utilization)
        optimal_metrics = ServiceMetrics(
            service_name="test-service",
            timestamp=datetime.now(),
            cpu_usage=65.0,
            memory_usage=65.0,
            request_rate=100.0,
            error_rate=1.0,
            latency_p50=50.0,
            latency_p95=100.0,
            latency_p99=200.0,
            active_connections=100,
            queue_depth=10,
        )

        decision = scaling_engine.calculate_optimal_instances(
            "test-service", optimal_metrics, current_instances
        )

        assert decision.direction == ScalingDirection.STABLE
        assert decision.target_instances == current_instances

    def test_calculate_optimal_instances_latency_trigger(self, scaling_engine):
        # Normal utilization but high latency
        metrics = ServiceMetrics(
            service_name="test-service",
            timestamp=datetime.now(),
            cpu_usage=60.0,
            memory_usage=60.0,
            request_rate=100.0,
            error_rate=1.0,
            latency_p50=500.0,
            latency_p95=1200.0,
            latency_p99=2500.0,  # Very high
            active_connections=100,
            queue_depth=10,
        )

        decision = scaling_engine.calculate_optimal_instances("test-service", metrics, 2)

        assert decision.direction == ScalingDirection.UP
        assert "High latency" in decision.reason


# --- IntelligentRouter Tests ---


class TestIntelligentRouter:
    def test_select_instance_none_available(self, intelligent_router):
        assert intelligent_router.select_instance("test-service", []) is None

    def test_select_instance_prefers_healthy(self, intelligent_router):
        healthy = ServiceInstance(
            instance_id="healthy-1", service_name="test-service", status=ServiceHealth.HEALTHY
        )
        degraded = ServiceInstance(
            instance_id="degraded-1", service_name="test-service", status=ServiceHealth.DEGRADED
        )

        selected = intelligent_router.select_instance("test-service", [healthy, degraded])
        assert selected.instance_id == "healthy-1"

    def test_select_instance_fallback_degraded(self, intelligent_router):
        degraded = ServiceInstance(
            instance_id="degraded-1", service_name="test-service", status=ServiceHealth.DEGRADED
        )

        selected = intelligent_router.select_instance("test-service", [degraded])
        assert selected.instance_id == "degraded-1"

    def test_calculate_instance_score(self, intelligent_router):
        instance = ServiceInstance(
            instance_id="inst-1", service_name="test-service", status=ServiceHealth.HEALTHY
        )
        # Add good metrics
        metrics = ServiceMetrics(
            service_name="test-service",
            timestamp=datetime.now(),
            cpu_usage=20.0,  # Good
            memory_usage=20.0,  # Good
            request_rate=10.0,
            error_rate=0.0,  # Good
            latency_p50=10.0,
            latency_p95=20.0,  # Good
            latency_p99=50.0,
            active_connections=10,
            queue_depth=0,
        )
        instance.metrics_history.append(metrics)

        score = intelligent_router._calculate_instance_score(instance)
        assert score > 0.5  # Should be a good score

    def test_update_instance_score(self, intelligent_router):
        instance_id = "inst-1"
        intelligent_router.update_instance_score(instance_id, success=True, response_time=100.0)
        assert intelligent_router.instance_scores[instance_id] > 0.5

        intelligent_router.update_instance_score(instance_id, success=False, response_time=500.0)
        # Should decrease, but start from previous value
        assert intelligent_router.instance_scores[instance_id] < 0.6  # Just a rough check


# --- PredictiveHealthMonitor Tests ---


class TestPredictiveHealthMonitor:
    def test_analyze_health_healthy(self, health_monitor, sample_metrics):
        status, warnings = health_monitor.analyze_health("test-service", sample_metrics)
        assert status == ServiceHealth.HEALTHY
        assert len(warnings) == 0

    def test_analyze_health_critical(self, health_monitor, high_load_metrics):
        # Make it really critical
        high_load_metrics.cpu_usage = 98.0
        status, warnings = health_monitor.analyze_health("test-service", high_load_metrics)
        assert status == ServiceHealth.CRITICAL
        assert len(warnings) > 0

    def test_analyze_health_degraded(self, health_monitor):
        metrics = ServiceMetrics(
            service_name="test-service",
            timestamp=datetime.now(),
            cpu_usage=88.0,  # > 85
            memory_usage=50.0,
            request_rate=100.0,
            error_rate=1.0,
            latency_p50=50.0,
            latency_p95=100.0,
            latency_p99=200.0,
            active_connections=100,
            queue_depth=10,
        )
        status, warnings = health_monitor.analyze_health("test-service", metrics)
        assert status == ServiceHealth.DEGRADED
        assert "High CPU usage" in warnings[0]

    def test_detect_anomalies(self, health_monitor, sample_metrics):
        # Populate history with consistent values but slight noise to ensure stdev > 0
        for i in range(35):
            noise = (i % 2) * 0.1
            m = ServiceMetrics(
                service_name="test-service",
                timestamp=datetime.now(),
                cpu_usage=20.0 + noise,
                memory_usage=20.0,
                request_rate=50.0,
                error_rate=0.0,
                latency_p50=20.0,
                latency_p95=30.0,
                latency_p99=50.0,
                active_connections=20,
                queue_depth=0,
            )
            health_monitor.health_patterns["test-service"].append(m)

        # Test with anomalous metric
        anomaly_metric = ServiceMetrics(
            service_name="test-service",
            timestamp=datetime.now(),
            cpu_usage=80.0,  # Sudden spike
            memory_usage=20.0,
            request_rate=50.0,
            error_rate=0.0,
            latency_p50=20.0,
            latency_p95=30.0,
            latency_p99=50.0,
            active_connections=20,
            queue_depth=0,
        )

        anomalies = health_monitor._detect_anomalies("test-service", anomaly_metric)
        assert len(anomalies) > 0
        assert "ANOMALY: cpu_usage" in anomalies[0]

    def test_predict_failure(self, health_monitor):
        # Create a trend of increasing error rates
        for i in range(15):
            m = ServiceMetrics(
                service_name="test-service",
                timestamp=datetime.now(),
                cpu_usage=50.0,
                memory_usage=50.0,
                request_rate=100.0,
                error_rate=1.0 + (i * 2.0),  # increasing errors
                latency_p50=50.0,
                latency_p95=100.0,
                latency_p99=200.0,
                active_connections=100,
                queue_depth=10,
            )
            health_monitor.health_patterns["test-service"].append(m)

        prob, factors = health_monitor.predict_failure("test-service")
        assert prob > 0
        assert any("Errors trending up" in f for f in factors)


# --- SelfAdaptiveMicroservices Tests ---


class TestSelfAdaptiveMicroservices:
    def test_register_service(self, adaptive_system):
        instances = adaptive_system.register_service("new-service", 3)
        assert len(instances) == 3
        assert instances[0].service_name == "new-service"
        assert instances[0].status == ServiceHealth.HEALTHY

    def test_update_metrics_and_health(self, adaptive_system, sample_metrics):
        adaptive_system.register_service("test-service", 1)
        instance_id = "test-service-0"

        adaptive_system.update_metrics("test-service", instance_id, sample_metrics)

        instance = adaptive_system.services["test-service"][0]
        assert len(instance.metrics_history) == 1
        assert instance.status == ServiceHealth.HEALTHY

    def test_auto_scale_up(self, adaptive_system, high_load_metrics):
        adaptive_system.register_service("test-service", 1)
        instance = adaptive_system.services["test-service"][0]

        # Add high load metrics to the instance
        instance.metrics_history.append(high_load_metrics)

        # Patch the scaling engine to ensure it returns UP
        with patch.object(
            adaptive_system.scaling_engine, "calculate_optimal_instances"
        ) as mock_calc:
            mock_calc.return_value = ScalingDecision(
                service_name="test-service",
                direction=ScalingDirection.UP,
                current_instances=1,
                target_instances=3,
                confidence=0.9,
                reason="High load",
                predicted_impact={},
                timestamp=datetime.now(),
            )

            decision = adaptive_system.auto_scale("test-service")

            assert decision.direction == ScalingDirection.UP
            assert len(adaptive_system.services["test-service"]) == 3

    def test_auto_scale_down(self, adaptive_system, low_load_metrics):
        adaptive_system.register_service("test-service", 3)
        # Populate all instances with low metrics
        for inst in adaptive_system.services["test-service"]:
            inst.metrics_history.append(low_load_metrics)

        with patch.object(
            adaptive_system.scaling_engine, "calculate_optimal_instances"
        ) as mock_calc:
            mock_calc.return_value = ScalingDecision(
                service_name="test-service",
                direction=ScalingDirection.DOWN,
                current_instances=3,
                target_instances=1,
                confidence=0.9,
                reason="Low load",
                predicted_impact={},
                timestamp=datetime.now(),
            )

            decision = adaptive_system.auto_scale("test-service")

            assert decision.direction == ScalingDirection.DOWN
            assert len(adaptive_system.services["test-service"]) == 1

    def test_route_request(self, adaptive_system):
        adaptive_system.register_service("test-service", 1)
        instance = adaptive_system.route_request("test-service")
        assert instance is not None
        assert instance.instance_id == "test-service-0"

    def test_get_service_status(self, adaptive_system):
        adaptive_system.register_service("test-service", 2)
        status = adaptive_system.get_service_status("test-service")

        assert status["service_name"] == "test-service"
        assert status["total_instances"] == 2
        assert status["healthy_instances"] == 2
        assert status["overall_health"] == "healthy"

    def test_aggregate_metrics(self, adaptive_system, sample_metrics):
        metrics_list = [sample_metrics, sample_metrics]
        aggregated = adaptive_system._aggregate_metrics("test-service", metrics_list)

        # Mean of identical metrics should be the same
        assert aggregated.cpu_usage == sample_metrics.cpu_usage
        # Request rate should be sum
        assert aggregated.request_rate == sample_metrics.request_rate * 2
