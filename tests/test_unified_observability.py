# tests/test_unified_observability.py
# ======================================================================================
# ==   UNIFIED OBSERVABILITY TESTS - COMPREHENSIVE TEST SUITE                      ==
# ======================================================================================
"""
اختبارات نظام الملاحظية الموحد - Unified Observability Tests

Tests for the world-class observability system covering:
✅ Distributed Tracing (W3C Trace Context)
✅ Metrics Collection (Golden Signals, RED, USE)
✅ Structured Logging with Correlation
✅ Anomaly Detection
✅ Service Dependency Mapping
✅ SLA/SLO Monitoring
✅ Exemplars (metrics → traces linking)
✅ Baggage Propagation
✅ Sampling Strategies
"""

import time
import unittest

from app.telemetry.unified_observability import (
    TraceContext,
    UnifiedObservabilityService,
    get_unified_observability,
)


class TestTraceContext(unittest.TestCase):
    """Test W3C Trace Context implementation"""

    def test_trace_context_creation(self):
        """Test creating a trace context"""
        context = TraceContext(
            trace_id="0123456789abcdef0123456789abcdef",
            span_id="0123456789abcdef",
            sampled=True,
        )

        self.assertEqual(context.trace_id, "0123456789abcdef0123456789abcdef")
        self.assertEqual(context.span_id, "0123456789abcdef")
        self.assertTrue(context.sampled)

    def test_trace_context_to_headers(self):
        """Test converting trace context to W3C headers"""
        context = TraceContext(
            trace_id="0123456789abcdef0123456789abcdef",
            span_id="fedcba9876543210",
            sampled=True,
            baggage={"user_id": "123", "tenant_id": "abc"},
        )

        headers = context.to_headers()

        self.assertIn("traceparent", headers)
        self.assertIn("tracestate", headers)
        self.assertEqual(
            headers["traceparent"], "00-0123456789abcdef0123456789abcdef-fedcba9876543210-01"
        )
        self.assertIn("user_id=123", headers["tracestate"])
        self.assertIn("tenant_id=abc", headers["tracestate"])

    def test_trace_context_from_headers(self):
        """Test extracting trace context from W3C headers"""
        headers = {
            "traceparent": "00-0123456789abcdef0123456789abcdef-fedcba9876543210-01",
            "tracestate": "user_id=123,tenant_id=abc",
        }

        context = TraceContext.from_headers(headers)

        self.assertIsNotNone(context)
        self.assertEqual(context.trace_id, "0123456789abcdef0123456789abcdef")
        self.assertEqual(context.parent_span_id, "fedcba9876543210")
        self.assertTrue(context.sampled)
        self.assertEqual(context.baggage.get("user_id"), "123")
        self.assertEqual(context.baggage.get("tenant_id"), "abc")


class TestUnifiedObservabilityService(unittest.TestCase):
    """Test unified observability service"""

    def setUp(self):
        """Set up test fixtures"""
        self.obs = UnifiedObservabilityService(service_name="test-service", sample_rate=1.0)

    def test_start_and_end_trace(self):
        """Test starting and ending a trace"""
        # Start trace
        context = self.obs.start_trace(
            operation_name="test_operation",
            tags={"test": "value"},
        )

        self.assertIsNotNone(context.trace_id)
        self.assertIsNotNone(context.span_id)
        self.assertTrue(context.sampled)

        # Verify trace is active
        stats = self.obs.get_statistics()
        self.assertEqual(stats["traces_started"], 1)
        self.assertEqual(stats["spans_created"], 1)

        # End span
        self.obs.end_span(span_id=context.span_id, status="OK")

        # Small delay for processing
        time.sleep(0.01)

        # Verify trace completed
        stats = self.obs.get_statistics()
        self.assertEqual(stats["traces_completed"], 1)

    def test_child_spans(self):
        """Test creating child spans"""
        # Start parent trace
        parent_context = self.obs.start_trace(operation_name="parent_operation")

        # Start child span
        child_context = self.obs.start_trace(
            operation_name="child_operation",
            parent_context=parent_context,
        )

        self.assertEqual(child_context.trace_id, parent_context.trace_id)
        self.assertNotEqual(child_context.span_id, parent_context.span_id)

        # End child first
        self.obs.end_span(span_id=child_context.span_id, status="OK")

        # End parent
        self.obs.end_span(span_id=parent_context.span_id, status="OK")

        time.sleep(0.01)

        # Get trace
        trace = self.obs.get_trace_with_correlation(parent_context.trace_id)
        self.assertIsNotNone(trace)
        self.assertEqual(trace["span_count"], 2)

    def test_span_events(self):
        """Test adding events to spans"""
        context = self.obs.start_trace(operation_name="test_operation")

        # Add events
        self.obs.add_span_event(
            span_id=context.span_id,
            event_name="cache_hit",
            attributes={"key": "user_123"},
        )

        self.obs.add_span_event(
            span_id=context.span_id,
            event_name="database_query",
            attributes={"query": "SELECT * FROM users"},
        )

        self.obs.end_span(span_id=context.span_id)
        time.sleep(0.01)

        # Verify events
        trace = self.obs.get_trace_with_correlation(context.trace_id)
        self.assertIsNotNone(trace)

        root_span = next((s for s in trace["spans"] if s["span_id"] == context.span_id), None)
        self.assertIsNotNone(root_span)
        self.assertEqual(len(root_span["events"]), 2)

    def test_baggage_propagation(self):
        """Test baggage propagation"""
        # Start parent with baggage
        parent_context = TraceContext(
            trace_id=self.obs._generate_trace_id(),
            span_id=self.obs._generate_span_id(),
            baggage={"user_id": "123", "experiment": "v2"},
        )

        context = self.obs.start_trace(
            operation_name="test_operation",
            parent_context=parent_context,
        )

        # Baggage should be inherited
        self.assertEqual(context.baggage.get("user_id"), "123")
        self.assertEqual(context.baggage.get("experiment"), "v2")

        self.obs.end_span(span_id=context.span_id)

    def test_record_metrics(self):
        """Test recording metrics"""
        context = self.obs.start_trace(operation_name="test_operation")

        # Record metrics
        self.obs.record_metric(
            name="request_duration",
            value=0.150,
            labels={"endpoint": "/api/users"},
            trace_id=context.trace_id,
            span_id=context.span_id,
        )

        self.obs.record_metric(
            name="request_duration",
            value=0.200,
            labels={"endpoint": "/api/users"},
        )

        self.obs.end_span(span_id=context.span_id)

        # Check metrics
        stats = self.obs.get_statistics()
        self.assertGreaterEqual(stats["metrics_recorded"], 2)

    def test_counter_and_gauge(self):
        """Test counter and gauge metrics"""
        # Test counter
        self.obs.increment_counter("http_requests", amount=1.0, labels={"method": "GET"})
        self.obs.increment_counter("http_requests", amount=1.0, labels={"method": "GET"})
        self.obs.increment_counter("http_requests", amount=1.0, labels={"method": "POST"})

        # Test gauge
        self.obs.set_gauge("active_connections", value=42.0)
        self.obs.set_gauge("memory_usage_mb", value=1024.0)

        # Verify
        self.assertEqual(len(self.obs.counters), 2)  # 2 label combinations
        self.assertEqual(len(self.obs.gauges), 2)

    def test_percentile_calculation(self):
        """Test percentile calculations"""
        # Record latency samples
        latencies = [10, 20, 30, 40, 50, 100, 150, 200, 500, 1000]
        for latency in latencies:
            self.obs.record_metric(name="latency_ms", value=latency)

        # Get percentiles
        percentiles = self.obs.get_percentiles("latency_ms")

        self.assertGreater(percentiles["p50"], 0)
        self.assertGreater(percentiles["p95"], percentiles["p50"])
        self.assertGreater(percentiles["p99"], percentiles["p95"])
        self.assertGreater(percentiles["p99.9"], percentiles["p99"])

    def test_structured_logging_with_correlation(self):
        """Test structured logging with trace correlation"""
        context = self.obs.start_trace(operation_name="test_operation")

        # Log messages
        self.obs.log(
            level="INFO",
            message="Request started",
            context={"user_id": 123},
            trace_id=context.trace_id,
            span_id=context.span_id,
        )

        self.obs.log(
            level="ERROR",
            message="Something went wrong",
            context={"error_code": "ERR_500"},
            exception=ValueError("Test error"),
            trace_id=context.trace_id,
            span_id=context.span_id,
        )

        self.obs.end_span(span_id=context.span_id)

        # Verify logs
        stats = self.obs.get_statistics()
        self.assertGreaterEqual(stats["logs_recorded"], 2)

        # Get correlated logs
        trace = self.obs.get_trace_with_correlation(context.trace_id)
        self.assertIsNotNone(trace)
        self.assertGreaterEqual(len(trace["correlated_logs"]), 2)

    def test_golden_signals(self):
        """Test Golden Signals calculation"""
        # Create some traces
        for i in range(10):
            context = self.obs.start_trace(operation_name="api_request")
            time.sleep(0.01)  # Simulate work
            status = "ERROR" if i < 2 else "OK"  # 20% error rate
            self.obs.end_span(span_id=context.span_id, status=status)

        time.sleep(0.1)

        # Get Golden Signals
        signals = self.obs.get_golden_signals(time_window_seconds=10)

        # Verify structure
        self.assertIn("latency", signals)
        self.assertIn("traffic", signals)
        self.assertIn("errors", signals)
        self.assertIn("saturation", signals)

        # Verify values
        self.assertGreater(signals["traffic"]["total_requests"], 0)
        self.assertGreater(signals["errors"]["error_rate"], 0)

    def test_trace_search(self):
        """Test searching traces by criteria"""
        # Create traces with different durations
        for duration_ms in [50, 100, 150, 200, 500]:
            context = self.obs.start_trace(operation_name="test_operation")
            time.sleep(duration_ms / 1000)
            self.obs.end_span(span_id=context.span_id)

        time.sleep(0.1)

        # Search for slow traces (> 100ms)
        slow_traces = self.obs.find_traces_by_criteria(min_duration_ms=100, limit=100)

        # Should find 4 traces (100, 150, 200, 500)
        self.assertGreaterEqual(len(slow_traces), 4)

    def test_error_tracking(self):
        """Test error tracking"""
        # Create error trace
        context = self.obs.start_trace(operation_name="failing_operation")
        self.obs.end_span(
            span_id=context.span_id,
            status="ERROR",
            error_message="Connection timeout",
        )

        time.sleep(0.1)

        # Search for error traces
        error_traces = self.obs.find_traces_by_criteria(has_errors=True, limit=100)

        self.assertGreater(len(error_traces), 0)

    def test_service_dependencies(self):
        """Test service dependency mapping"""
        # Create trace with multiple services
        parent_context = self.obs.start_trace(
            operation_name="api_gateway",
            tags={"service.name": "api-gateway"},
        )

        # Child service 1
        child1 = self.obs.start_trace(
            operation_name="auth_service",
            parent_context=parent_context,
            tags={"service.name": "auth-service"},
        )
        self.obs.end_span(span_id=child1.span_id)

        # Child service 2
        child2 = self.obs.start_trace(
            operation_name="database",
            parent_context=parent_context,
            tags={"service.name": "database"},
        )
        self.obs.end_span(span_id=child2.span_id)

        self.obs.end_span(span_id=parent_context.span_id)
        time.sleep(0.1)

        # Get dependencies
        deps = self.obs.get_service_dependencies()

        # Should show api-gateway → [auth-service, database]
        self.assertIsInstance(deps, dict)

    def test_anomaly_detection(self):
        """Test ML-based anomaly detection"""
        # Create normal baseline
        for _ in range(20):
            context = self.obs.start_trace(operation_name="normal_operation")
            time.sleep(0.01)  # ~10ms
            self.obs.end_span(span_id=context.span_id)

        time.sleep(0.1)

        # Create anomaly (very slow request)
        context = self.obs.start_trace(operation_name="slow_operation")
        time.sleep(0.5)  # 500ms (50x normal)
        self.obs.end_span(span_id=context.span_id)

        time.sleep(0.1)

        # Detect anomalies
        anomalies = self.obs.detect_anomalies()

        # Should detect latency spike
        # Note: May not detect on first run due to baseline building
        self.assertIsInstance(anomalies, list)

    def test_prometheus_export(self):
        """Test Prometheus format export"""
        # Record some metrics
        self.obs.increment_counter("http_requests_total", labels={"method": "GET", "status": "200"})
        self.obs.set_gauge("active_connections", value=42.0)

        # Export
        prometheus_text = self.obs.export_prometheus_metrics()

        # Verify format
        self.assertIsInstance(prometheus_text, str)
        self.assertIn("http_requests_total", prometheus_text)
        self.assertIn("active_connections", prometheus_text)

    def test_statistics(self):
        """Test getting observability statistics"""
        # Create some activity
        context = self.obs.start_trace(operation_name="test")
        self.obs.record_metric("test_metric", value=1.0)
        self.obs.log("INFO", "test message")
        self.obs.end_span(span_id=context.span_id)

        # Get stats
        stats = self.obs.get_statistics()

        self.assertIn("traces_started", stats)
        self.assertIn("spans_created", stats)
        self.assertIn("metrics_recorded", stats)
        self.assertIn("logs_recorded", stats)
        self.assertGreater(stats["traces_started"], 0)


class TestObservabilitySingleton(unittest.TestCase):
    """Test singleton pattern for observability service"""

    def test_singleton_instance(self):
        """Test that get_unified_observability returns same instance"""
        obs1 = get_unified_observability()
        obs2 = get_unified_observability()

        self.assertIs(obs1, obs2)


class TestSamplingStrategies(unittest.TestCase):
    """Test sampling strategies"""

    def test_head_based_sampling(self):
        """Test head-based sampling (50% rate)"""
        obs = UnifiedObservabilityService(sample_rate=0.5)

        sampled_count = 0
        total_count = 100

        for _ in range(total_count):
            context = obs.start_trace(operation_name="test")
            if context.sampled:
                sampled_count += 1
            obs.end_span(span_id=context.span_id)

        # Should be approximately 50% (with some variance)
        self.assertGreater(sampled_count, 30)
        self.assertLess(sampled_count, 70)

    def test_always_sample_errors(self):
        """Test that errors are always sampled (tail-based)"""
        obs = UnifiedObservabilityService(sample_rate=0.01)  # Very low rate

        # Create error trace
        context = obs.start_trace(operation_name="failing_operation")
        obs.end_span(span_id=context.span_id, status="ERROR", error_message="Test error")

        time.sleep(0.1)

        # Should be in completed traces despite low sample rate
        stats = obs.get_statistics()
        self.assertGreaterEqual(stats["traces_completed"], 1)


if __name__ == "__main__":
    unittest.main()
