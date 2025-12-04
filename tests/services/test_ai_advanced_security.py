from datetime import datetime

import pytest

from app.services.ai_advanced_security import (
    AutomatedResponseSystem,
    BehavioralAnalyzer,
    DeepLearningThreatDetector,
    SecurityEvent,
    SuperhumanSecuritySystem,
    ThreatLevel,
    ThreatType,
    UserBehaviorProfile,
)


@pytest.fixture
def security_system():
    return SuperhumanSecuritySystem()


@pytest.fixture
def sample_event():
    return SecurityEvent(
        event_id="evt_001",
        timestamp=datetime.now(),
        source_ip="192.168.1.100",
        user_id="user_123",
        event_type="api_request",
        endpoint="/api/v1/users",
        method="GET",
        payload={},
        headers={"User-Agent": "Mozilla/5.0"},
        response_code=200,
        response_time=0.045,
    )


class TestDeepLearningThreatDetector:
    def test_detect_sql_injection_payload(self, sample_event):
        detector = DeepLearningThreatDetector()
        sample_event.payload = {"query": "SELECT * FROM users WHERE id=1 OR 1=1"}
        threats = detector.analyze_request(sample_event)

        assert len(threats) > 0
        assert threats[0].threat_type == ThreatType.SQL_INJECTION
        assert threats[0].threat_level == ThreatLevel.CRITICAL
        assert threats[0].auto_blocked is True

    def test_detect_sql_injection_url(self, sample_event):
        detector = DeepLearningThreatDetector()
        # Use a payload that clearly matches the SQL injection patterns
        sample_event.endpoint = "/api/v1/users?id=1 or 1=1"
        threats = detector.analyze_request(sample_event)

        assert len(threats) > 0
        assert threats[0].threat_type == ThreatType.SQL_INJECTION

    def test_detect_xss(self, sample_event):
        detector = DeepLearningThreatDetector()
        # Verify XSS detection
        sample_event.payload = {"comment": "<script>alert(1)</script>"}
        threats = detector.analyze_request(sample_event)

        assert len(threats) > 0
        threat_types = [t.threat_type for t in threats]
        assert ThreatType.XSS_ATTACK in threat_types

    def test_detect_malformed_request_code(self, sample_event):
        detector = DeepLearningThreatDetector()
        sample_event.response_code = 400
        threats = detector.analyze_request(sample_event)

        assert len(threats) > 0
        assert threats[0].threat_type == ThreatType.MALFORMED_REQUEST
        assert threats[0].threat_level == ThreatLevel.MEDIUM

    def test_detect_malformed_request_payload_size(self, sample_event):
        detector = DeepLearningThreatDetector()
        sample_event.payload = {"data": "a" * 10001}
        threats = detector.analyze_request(sample_event)

        assert len(threats) > 0
        assert threats[0].threat_type == ThreatType.MALFORMED_REQUEST


class TestBehavioralAnalyzer:
    def test_get_or_create_profile(self):
        analyzer = BehavioralAnalyzer()
        profile = analyzer._get_or_create_profile("user_123")
        assert isinstance(profile, UserBehaviorProfile)
        assert profile.user_id == "user_123"

    def test_detect_unusual_endpoint(self, sample_event):
        analyzer = BehavioralAnalyzer()
        # Initialize profile with some typical endpoints
        profile = analyzer._get_or_create_profile(sample_event.user_id)
        profile.typical_endpoints = ["/api/v1/home"]

        sample_event.endpoint = "/api/v1/admin/secret"
        threats = analyzer.analyze_behavior(sample_event)

        assert any(t.threat_type == ThreatType.ANOMALOUS_BEHAVIOR for t in threats)
        assert any("sensitive endpoint" in t.description for t in threats)

    def test_detect_unusual_time(self, sample_event):
        analyzer = BehavioralAnalyzer()
        profile = analyzer._get_or_create_profile(sample_event.user_id)
        # Set typical hour to be different from current hour
        current_hour = sample_event.timestamp.hour
        typical_hour = (current_hour + 12) % 24
        profile.typical_hours = [typical_hour]

        threats = analyzer.analyze_behavior(sample_event)

        assert any(t.threat_type == ThreatType.ANOMALOUS_BEHAVIOR for t in threats)
        assert any("unusual time" in t.description for t in threats)

    def test_detect_rapid_requests(self, sample_event):
        analyzer = BehavioralAnalyzer()
        user_id = sample_event.user_id

        # Simulate 101 requests within a minute
        for _ in range(101):
            analyzer.event_history[user_id].append(sample_event)

        threats = analyzer.analyze_behavior(sample_event)

        assert any(t.threat_type == ThreatType.BRUTE_FORCE for t in threats)

    def test_update_profile(self, sample_event):
        analyzer = BehavioralAnalyzer()
        analyzer.analyze_behavior(sample_event)

        profile = analyzer.user_profiles[sample_event.user_id]
        assert sample_event.endpoint in profile.typical_endpoints
        assert sample_event.timestamp.hour in profile.typical_hours


class TestAutomatedResponseSystem:
    def test_block_ip(self):
        response_system = AutomatedResponseSystem()
        response_system._block_ip("192.168.1.100")
        blocked, reason = response_system.is_blocked("192.168.1.100")
        assert blocked is True
        assert "IP 192.168.1.100 is blocked" in reason

    def test_block_user(self):
        response_system = AutomatedResponseSystem()
        response_system._block_user("user_123")
        blocked, reason = response_system.is_blocked("192.168.1.100", "user_123")
        assert blocked is True
        assert "User user_123 is blocked" in reason

    def test_rate_limit(self):
        response_system = AutomatedResponseSystem()
        ip = "192.168.1.100"

        # Simulate > 50 requests in less than a minute
        for _ in range(51):
            response_system.rate_limits[ip].append(datetime.now())

        blocked, reason = response_system.is_blocked(ip)
        assert blocked is True
        assert "Rate limit exceeded" in reason

    def test_respond_to_critical_threat(self, sample_event):
        response_system = AutomatedResponseSystem()
        detector = DeepLearningThreatDetector()

        # Generate a critical threat (SQL Injection)
        sample_event.payload = {"query": "SELECT * FROM users WHERE id=1 OR 1=1"}
        threats = detector.analyze_request(sample_event)
        critical_threat = threats[0]

        result = response_system.respond_to_threat(critical_threat)

        assert "Blocked IP" in result["actions_taken"][0]
        blocked, _ = response_system.is_blocked(sample_event.source_ip)
        assert blocked is True


class TestSuperhumanSecuritySystem:
    def test_process_legitimate_request(self, security_system, sample_event):
        allowed, threats = security_system.process_request(sample_event)
        assert allowed is True
        assert len(threats) == 0

    def test_process_malicious_request(self, security_system, sample_event):
        sample_event.payload = {"query": "SELECT * FROM users WHERE id=1 OR 1=1"}
        allowed, threats = security_system.process_request(sample_event)

        assert allowed is False
        assert len(threats) > 0

        # Verify automatic blocking
        blocked, _ = security_system.response_system.is_blocked(sample_event.source_ip)
        assert blocked is True

    def test_security_dashboard(self, security_system, sample_event):
        # Process some events
        security_system.process_request(sample_event)  # Legitimate

        malicious_event = SecurityEvent(
            event_id="evt_002",
            timestamp=datetime.now(),
            source_ip="10.0.0.50",
            user_id="bad_user",
            event_type="api_request",
            endpoint="/api/v1/users",
            method="POST",
            payload={"query": "SELECT * FROM users --"},
            headers={},
            response_code=200,
            response_time=0.1,
        )
        security_system.process_request(malicious_event)  # Malicious

        dashboard = security_system.get_security_dashboard()

        assert dashboard["statistics"]["total_events"] == 2
        assert dashboard["statistics"]["total_threats_detected"] >= 1
        assert dashboard["security_score"] < 100
