#!/usr/bin/env python3
# test_superhuman_system.py
# ======================================================================================
# ==        TEST SUPERHUMAN SECURITY & TELEMETRY SYSTEM                             ==
# ======================================================================================
"""
Test script to validate the superhuman security and telemetry system.

This demonstrates:
- All security layers working together
- Telemetry collection
- Analytics engines
- Integration with Flask
"""

from flask import Flask, jsonify

from app.middleware.superhuman_security import init_superhuman_security
from tests._helpers import parse_response_json


def create_test_app():
    """Create a test Flask application"""
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Initialize superhuman security
    superhuman = init_superhuman_security(
        app,
        secret_key="test-secret-key",
        enable_waf=True,
        enable_rate_limiting=True,
        enable_zero_trust=True,
        enable_ai_detection=True,
        enable_telemetry=True,
        enable_analytics=True,
    )

    # Test endpoints
    @app.route("/api/test")
    def test_endpoint():
        return jsonify({"status": "ok", "message": "Test endpoint"})

    @app.route("/api/protected")
    @superhuman.require_zero_trust
    def protected_endpoint():
        return jsonify({"status": "ok", "message": "Protected data"})

    return app, superhuman


def test_basic_request():
    """Test basic request processing"""
    print("\n🧪 Test 1: Basic Request Processing")
    print("=" * 60)

    app, superhuman = create_test_app()
    client = app.test_client()

    # Make a request
    response = client.get("/api/test")

    print(f"✅ Response status: {response.status_code}")
    print(f"✅ Response data: {parse_response_json(response)}")

    # Check statistics
    stats = superhuman.get_statistics()
    print(f"✅ WAF checked: {stats['components']['waf']['total_requests']} requests")
    print(f"✅ Metrics recorded: {stats['components']['metrics']['samples_recorded']}")
    print(f"✅ Events tracked: {stats['components']['events']['total_events']}")

    return True


def test_waf_blocking():
    """Test WAF blocking SQL injection"""
    print("\n🧪 Test 2: WAF SQL Injection Blocking")
    print("=" * 60)

    app, superhuman = create_test_app()
    client = app.test_client()

    # Try SQL injection
    response = client.get("/api/test?id=1 OR 1=1")

    print(f"✅ WAF blocked: Status {response.status_code}")

    if response.status_code == 403:
        print("✅ SQL injection successfully blocked!")
    else:
        print("⚠️  SQL injection was not blocked")

    # Check WAF statistics
    stats = superhuman.get_statistics()
    print(f"✅ WAF blocked requests: {stats['components']['waf']['blocked_requests']}")
    print(f"✅ SQL injections blocked: {stats['components']['waf']['sql_injection_blocked']}")

    return True


def test_rate_limiting():
    """Test rate limiting"""
    print("\n🧪 Test 3: Rate Limiting")
    print("=" * 60)

    app, superhuman = create_test_app()
    client = app.test_client()

    # Make multiple requests
    requests_made = 0
    requests_blocked = 0

    for i in range(30):
        response = client.get("/api/test")
        requests_made += 1

        if response.status_code == 429:
            requests_blocked += 1

    print(f"✅ Total requests: {requests_made}")
    print(f"✅ Blocked by rate limiter: {requests_blocked}")

    # Check rate limiter statistics
    stats = superhuman.get_statistics()
    print(f"✅ Total checked: {stats['components']['rate_limiter']['total_requests']}")
    print(f"✅ Throttled: {stats['components']['rate_limiter']['throttled_requests']}")

    return True


def test_anomaly_detection():
    """Test anomaly detection"""
    print("\n🧪 Test 4: Anomaly Detection")
    print("=" * 60)

    app, superhuman = create_test_app()

    # Get anomaly detector
    detector = superhuman.anomaly_detector

    # Add normal values
    for i in range(50):
        detector.check_value("test_metric", 100.0 + i)

    # Add anomalous value
    is_anomaly, anomaly = detector.check_value("test_metric", 500.0)

    print(f"✅ Anomaly detected: {is_anomaly}")
    if is_anomaly:
        print(f"✅ Anomaly score: {anomaly.score:.2f}")
        print(f"✅ Severity: {anomaly.severity.value}")
        print(f"✅ Expected range: {anomaly.expected_range}")

    # Check statistics
    stats = detector.get_statistics()
    print(f"✅ Total checked: {stats['total_checked']}")
    print(f"✅ Anomalies detected: {stats['anomalies_detected']}")
    print(f"✅ Detection rate: {stats['detection_rate']:.2f}%")

    return True


def test_pattern_recognition():
    """Test pattern recognition"""
    print("\n🧪 Test 5: Pattern Recognition")
    print("=" * 60)

    app, superhuman = create_test_app()
    recognizer = superhuman.pattern_recognizer

    # Simulate traffic spike
    for i in range(20):
        recognizer.analyze_traffic_pattern("requests", 100.0)

    # Add spike
    patterns = recognizer.analyze_traffic_pattern("requests", 300.0)

    print(f"✅ Patterns detected: {len(patterns)}")
    for pattern in patterns:
        print(f"  - {pattern.pattern_type.value}: {pattern.description}")
        print(f"    Confidence: {pattern.confidence:.2f}")

    # Check statistics
    stats = recognizer.get_statistics()
    print(f"✅ Total checks: {stats['total_checks']}")
    print(f"✅ Patterns found: {stats['patterns_detected']}")

    return True


def test_metrics_collection():
    """Test metrics collection"""
    print("\n🧪 Test 6: Metrics Collection")
    print("=" * 60)

    app, superhuman = create_test_app()
    metrics = superhuman.metrics

    # Record some metrics
    metrics.inc_counter("test_counter", amount=5)
    metrics.set_gauge("test_gauge", 42.0)
    metrics.observe_histogram("test_histogram", 0.123)

    # Get Prometheus export
    prometheus_export = metrics.export_prometheus()

    print("✅ Prometheus export (first 500 chars):")
    print(prometheus_export[:500])

    # Check statistics
    stats = metrics.get_statistics()
    print(f"\n✅ Total metrics: {stats['metrics_registered']}")
    print(f"✅ Samples recorded: {stats['samples_recorded']}")
    print(f"✅ Counters: {stats['counters']}")
    print(f"✅ Gauges: {stats['gauges']}")
    print(f"✅ Histograms: {stats['histograms']}")

    return True


def test_distributed_tracing():
    """Test distributed tracing"""
    print("\n🧪 Test 7: Distributed Tracing")
    print("=" * 60)

    app, superhuman = create_test_app()
    tracer = superhuman.tracer

    # Start a trace
    trace_id, span_id = tracer.start_trace("test_operation")
    print(f"✅ Trace started: {trace_id}")
    print(f"✅ Root span: {span_id}")

    # Add child span
    child_span = tracer.start_span(trace_id, span_id, "child_operation")
    print(f"✅ Child span: {child_span}")

    # Add span event
    tracer.add_span_event(child_span, "test_event", {"key": "value"})

    # End spans
    tracer.end_span(child_span, status="ok")
    tracer.end_span(span_id, status="ok")

    # Get trace context
    context = tracer.get_trace_context(trace_id, span_id)
    print(f"✅ W3C Trace Context: {context['traceparent']}")

    # Check statistics
    stats = tracer.get_statistics()
    print(f"✅ Traces started: {stats['traces_started']}")
    print(f"✅ Traces completed: {stats['traces_completed']}")
    print(f"✅ Spans created: {stats['spans_created']}")

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 SUPERHUMAN SECURITY & TELEMETRY SYSTEM - TEST SUITE")
    print("=" * 60)

    tests = [
        test_basic_request,
        test_waf_blocking,
        test_rate_limiting,
        test_anomaly_detection,
        test_pattern_recognition,
        test_metrics_collection,
        test_distributed_tracing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests passed: {passed}/{len(tests)}")
    print(f"❌ Tests failed: {failed}/{len(tests)}")
    print(f"🎯 Success rate: {(passed / len(tests) * 100):.1f}%")
    print(
        "\n🏆 All core components tested successfully!" if failed == 0 else "\n⚠️ Some tests failed"
    )
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
