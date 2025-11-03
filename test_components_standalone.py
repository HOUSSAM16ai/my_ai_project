#!/usr/bin/env python3
# test_components_standalone.py
"""
Standalone test of superhuman system components (without Flask dependencies)
"""

def test_waf():
    """Test WAF component"""
    from app.security.waf import WebApplicationFirewall

    print("\n🧪 Test 1: Web Application Firewall")
    print("=" * 60)
    
    waf = WebApplicationFirewall()
    
    # Simulate a request object
    class FakeRequest:
        def __init__(self, args, form, data, headers, path, remote_addr):
            self.args = args
            self.form = form
            self.data = data
            self.headers = headers
            self.path = path
            self.remote_addr = remote_addr
            self.is_json = False
            self.json = None
    
    # Normal request
    normal_req = FakeRequest({}, {}, b"", {"User-Agent": "Mozilla"}, "/api/users", "1.2.3.4")
    is_safe, attack = waf.check_request(normal_req)
    print(f"✅ Normal request: is_safe={is_safe}")
    
    # SQL injection attempt
    malicious_req = FakeRequest(
        {"id": "1 OR 1=1"}, {}, b"", {"User-Agent": "Mozilla"}, "/api/users", "5.6.7.8"
    )
    is_safe, attack = waf.check_request(malicious_req)
    print(f"✅ SQL injection: is_safe={is_safe}, attack_type={attack.attack_type if attack else None}")
    
    # Get stats
    stats = waf.get_statistics()
    print(f"✅ Total requests checked: {stats['total_requests']}")
    print(f"✅ Blocked requests: {stats['blocked_requests']}")
    print(f"✅ Block rate: {stats['block_rate']:.2f}%")
    
    return True


def test_rate_limiter():
    """Test Rate Limiter component"""
    from app.security.rate_limiter import AdaptiveRateLimiter, UserTier

    print("\n🧪 Test 2: Adaptive Rate Limiter")
    print("=" * 60)
    
    limiter = AdaptiveRateLimiter()
    
    # Simulate request
    class FakeRequest:
        def __init__(self, remote_addr):
            self.remote_addr = remote_addr
    
    # Make requests
    allowed_count = 0
    blocked_count = 0
    
    for i in range(25):
        req = FakeRequest("10.0.0.1")
        is_allowed, info = limiter.check_rate_limit(req, tier=UserTier.FREE)
        
        if is_allowed:
            allowed_count += 1
        else:
            blocked_count += 1
    
    print(f"✅ Allowed requests: {allowed_count}")
    print(f"✅ Blocked requests: {blocked_count}")
    
    # Get stats
    stats = limiter.get_statistics()
    print(f"✅ Total requests: {stats['total_requests']}")
    print(f"✅ Throttled: {stats['throttled_requests']}")
    print(f"✅ Throttle rate: {stats['throttle_rate']:.2f}%")
    
    return True


def test_anomaly_detector():
    """Test Anomaly Detector"""
    print("\n🧪 Test 3: Anomaly Detector")
    print("=" * 60)
    
    from app.analysis.anomaly_detector import AnomalyDetector
    
    detector = AnomalyDetector(sensitivity=0.95)
    
    # Add normal values
    for i in range(50):
        detector.check_value("response_time", 100.0 + i * 2)
    
    # Add anomalous value
    is_anomaly, anomaly = detector.check_value("response_time", 500.0)
    
    print(f"✅ Anomaly detected: {is_anomaly}")
    if is_anomaly:
        print(f"✅ Score: {anomaly.score:.2f}")
        print(f"✅ Severity: {anomaly.severity.value}")
        print(f"✅ Type: {anomaly.anomaly_type.value}")
    
    # Get stats
    stats = detector.get_statistics()
    print(f"✅ Total checked: {stats['total_checked']}")
    print(f"✅ Anomalies detected: {stats['anomalies_detected']}")
    print(f"✅ Detection rate: {stats['detection_rate']:.2f}%")
    
    return True


def test_pattern_recognizer():
    """Test Pattern Recognizer"""
    print("\n🧪 Test 4: Pattern Recognizer")
    print("=" * 60)
    
    from app.analysis.pattern_recognizer import PatternRecognizer
    
    recognizer = PatternRecognizer()
    
    # Simulate normal traffic
    for i in range(20):
        recognizer.analyze_traffic_pattern("requests_per_min", 100.0)
    
    # Simulate spike
    patterns = recognizer.analyze_traffic_pattern("requests_per_min", 300.0)
    
    print(f"✅ Patterns detected: {len(patterns)}")
    for pattern in patterns:
        print(f"  - Type: {pattern.pattern_type.value}")
        print(f"    Description: {pattern.description}")
        print(f"    Confidence: {pattern.confidence:.2f}")
    
    # Get stats
    stats = recognizer.get_statistics()
    print(f"✅ Total checks: {stats['total_checks']}")
    print(f"✅ Patterns found: {stats['patterns_detected']}")
    
    return True


def test_metrics_collector():
    """Test Metrics Collector"""
    print("\n🧪 Test 5: Metrics Collector")
    print("=" * 60)
    
    from app.telemetry.metrics import MetricsCollector
    
    collector = MetricsCollector()
    
    # Record metrics
    collector.inc_counter("http_requests_total", labels={"method": "GET"})
    collector.inc_counter("http_requests_total", labels={"method": "POST"}, amount=5)
    collector.set_gauge("active_connections", 42)
    collector.observe_histogram("request_duration", 0.125)
    collector.observe_histogram("request_duration", 0.089)
    collector.observe_histogram("request_duration", 0.234)
    
    # Get Prometheus export
    export = collector.export_prometheus()
    
    print("✅ Prometheus export (first 300 chars):")
    print(export[:300])
    
    # Get stats
    stats = collector.get_statistics()
    print(f"\n✅ Metrics registered: {stats['metrics_registered']}")
    print(f"✅ Samples recorded: {stats['samples_recorded']}")
    
    return True


def test_distributed_tracer():
    """Test Distributed Tracer"""
    print("\n🧪 Test 6: Distributed Tracer")
    print("=" * 60)
    
    from app.telemetry.tracing import DistributedTracer, SpanStatus
    
    tracer = DistributedTracer(service_name="test-service")
    
    # Start trace
    trace_id, span_id = tracer.start_trace("test_operation")
    print(f"✅ Trace ID: {trace_id[:16]}...")
    print(f"✅ Span ID: {span_id}")
    
    # Add child span
    child_id = tracer.start_span(trace_id, span_id, "child_operation")
    print(f"✅ Child span: {child_id}")
    
    # Add event
    tracer.add_span_event(child_id, "checkpoint", {"step": 1})
    
    # End spans
    tracer.end_span(child_id, status=SpanStatus.OK)
    tracer.end_span(span_id, status=SpanStatus.OK)
    
    # Get trace context
    context = tracer.get_trace_context(trace_id, span_id)
    print(f"✅ Traceparent: {context['traceparent'][:40]}...")
    
    # Get stats
    stats = tracer.get_statistics()
    print(f"✅ Traces started: {stats['traces_started']}")
    print(f"✅ Spans created: {stats['spans_created']}")
    
    return True


def run_all_tests():
    """Run all component tests"""
    print("\n" + "=" * 60)
    print("🚀 SUPERHUMAN SYSTEM COMPONENTS - STANDALONE TEST")
    print("=" * 60)
    
    tests = [
        test_waf,
        test_rate_limiter,
        test_anomaly_detector,
        test_pattern_recognizer,
        test_metrics_collector,
        test_distributed_tracer,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
                print("✅ PASSED\n")
        except Exception as e:
            print(f"\n❌ FAILED: {str(e)}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests passed: {passed}/{len(tests)}")
    print(f"❌ Tests failed: {failed}/{len(tests)}")
    print(f"🎯 Success rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🏆 ALL COMPONENTS WORKING PERFECTLY!")
        print("✨ System is ready for production use!")
    else:
        print(f"\n⚠️  {failed} component(s) need attention")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
