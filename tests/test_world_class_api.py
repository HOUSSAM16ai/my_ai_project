# tests/test_world_class_api.py
# ======================================================================================
# ==            TESTS FOR WORLD-CLASS API FEATURES (v2.0)                           ==
# ======================================================================================
# PRIME DIRECTIVE:
#   اختبارات شاملة للمميزات الخارقة - Comprehensive tests for superhuman features

import time

from app.services.api_contract_service import APIContractService
from app.services.api_observability_service import (
    APIObservabilityService,
)
from app.services.api_security_service import APISecurityService

# ======================================================================================
# OBSERVABILITY SERVICE TESTS
# ======================================================================================


class TestObservabilityService:
    """اختبارات خدمة المراقبة - Observability service tests"""

    def test_trace_generation(self):
        """Test distributed trace ID generation"""
        service = APIObservabilityService()

        trace_id1 = service.generate_trace_id()
        trace_id2 = service.generate_trace_id()

        assert trace_id1 != trace_id2
        assert len(trace_id1) == 16
        assert len(trace_id2) == 16

    def test_metrics_recording(self):
        """Test request metrics recording"""
        service = APIObservabilityService()

        # Record some metrics
        service.record_request_metrics(
            endpoint="/api/test", method="GET", status_code=200, duration_ms=15.5, user_id=1
        )

        service.record_request_metrics(
            endpoint="/api/test", method="GET", status_code=200, duration_ms=12.3, user_id=1
        )

        # Get snapshot
        snapshot = service.get_performance_snapshot()

        assert snapshot.avg_latency_ms > 0
        assert snapshot.p50_latency_ms > 0
        assert snapshot.requests_per_second >= 0

    def test_percentile_calculation(self):
        """Test latency percentile calculation"""
        service = APIObservabilityService()

        # Record metrics with known values
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for latency in latencies:
            service.record_request_metrics(
                endpoint="/api/test", method="GET", status_code=200, duration_ms=latency
            )

        snapshot = service.get_performance_snapshot()

        # P50 should be around 50
        assert 40 <= snapshot.p50_latency_ms <= 60
        # P95 should be around 95
        assert 85 <= snapshot.p95_latency_ms <= 100

    def test_anomaly_detection(self):
        """Test ML-based anomaly detection"""
        service = APIObservabilityService(sla_target_ms=20.0)

        # Record normal metrics
        for _ in range(10):
            service.record_request_metrics(
                endpoint="/api/test", method="GET", status_code=200, duration_ms=15.0
            )

        # Record anomalous metric (5x baseline)
        service.record_request_metrics(
            endpoint="/api/test", method="GET", status_code=200, duration_ms=150.0
        )

        # Check if alert was generated
        alerts = service.get_all_alerts(severity="critical")
        assert len(alerts) > 0

    def test_sla_compliance(self):
        """Test SLA compliance monitoring"""
        service = APIObservabilityService(sla_target_ms=20.0)

        # Record metrics within SLA
        for _ in range(8):
            service.record_request_metrics(
                endpoint="/api/test", method="GET", status_code=200, duration_ms=15.0
            )

        # Record metrics violating SLA
        for _ in range(2):
            service.record_request_metrics(
                endpoint="/api/test", method="GET", status_code=200, duration_ms=25.0
            )

        compliance = service.get_sla_compliance()

        assert compliance["total_requests"] == 10
        assert compliance["violations"] == 2
        assert compliance["compliance_rate_percent"] == 80.0

    def test_endpoint_analytics(self):
        """Test endpoint-specific analytics"""
        service = APIObservabilityService()

        endpoint = "/api/users"

        # Record some metrics
        for latency in [10, 15, 20, 25, 30]:
            service.record_request_metrics(
                endpoint=endpoint, method="GET", status_code=200, duration_ms=latency
            )

        analytics = service.get_endpoint_analytics(endpoint)

        assert analytics["status"] == "success"
        assert analytics["total_requests"] == 5
        assert analytics["avg_latency_ms"] == 20.0
        assert analytics["min_latency_ms"] == 10.0
        assert analytics["max_latency_ms"] == 30.0


# ======================================================================================
# SECURITY SERVICE TESTS
# ======================================================================================


class TestSecurityService:
    """اختبارات خدمة الأمان - Security service tests"""

    def test_jwt_token_generation(self):
        """Test JWT token generation"""
        service = APISecurityService()

        token = service.generate_access_token(user_id=1, scopes=["read", "write"])

        assert token.token is not None
        assert token.token_type == "access"
        assert token.user_id == 1
        assert token.scopes == ["read", "write"]
        assert len(token.jti) > 0

    def test_jwt_token_verification(self):
        """Test JWT token verification"""
        service = APISecurityService()

        # Generate token
        token = service.generate_access_token(user_id=1)

        # Verify token
        payload = service.verify_token(token.token)

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["type"] == "access"

    def test_token_revocation(self):
        """Test token revocation"""
        service = APISecurityService()

        # Generate token
        token = service.generate_access_token(user_id=1)

        # Verify it works
        payload1 = service.verify_token(token.token)
        assert payload1 is not None

        # Revoke token
        service.revoke_token(token.jti)

        # Verify it no longer works
        payload2 = service.verify_token(token.token)
        assert payload2 is None

    def test_token_rotation(self):
        """Test token rotation with refresh token"""
        service = APISecurityService()

        # Generate refresh token
        refresh_token = service.generate_refresh_token(user_id=1)

        # Rotate to get new access token
        new_access_token = service.rotate_token(refresh_token.token)

        assert new_access_token is not None
        assert new_access_token.user_id == 1
        assert new_access_token.token_type == "access"

    def test_request_signature_generation(self):
        """Test HMAC-SHA256 request signature"""
        service = APISecurityService()

        signature = service.generate_request_signature(
            method="POST",
            path="/api/test",
            timestamp=int(time.time()),
            nonce="test-nonce",
            body=b'{"data": "test"}',
            secret_key="test-secret",
        )

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest

    def test_request_signature_verification(self):
        """Test request signature verification"""
        service = APISecurityService()

        timestamp = int(time.time())
        nonce = "test-nonce"
        body = b'{"data": "test"}'

        # Generate signature
        signature = service.generate_request_signature(
            method="POST",
            path="/api/test",
            timestamp=timestamp,
            nonce=nonce,
            body=body,
            secret_key="test-secret",
        )

        # Verify signature
        is_valid = service.verify_request_signature(
            provided_signature=signature,
            method="POST",
            path="/api/test",
            timestamp=timestamp,
            nonce=nonce,
            body=body,
            secret_key="test-secret",
        )

        assert is_valid is True

    def test_rate_limiting(self):
        """Test adaptive rate limiting"""
        service = APISecurityService()

        client_id = "test-client"

        # First requests should be allowed
        for _ in range(10):
            allowed, _info = service.check_rate_limit(client_id)
            assert allowed is True

        # Get current state
        state = service.rate_limit_states[client_id]
        assert len(state.requests) == 10

    def test_rate_limit_blocking(self):
        """Test rate limit blocking on burst"""
        service = APISecurityService()

        client_id = "burst-client"

        # Exceed burst limit
        for _ in range(151):  # RATE_LIMIT_BURST = 150
            service.check_rate_limit(client_id)

        # Next request should be blocked
        allowed, info = service.check_rate_limit(client_id)
        assert allowed is False
        assert info["blocked"] is True
        assert "retry_after" in info

    def test_ip_blacklist(self):
        """Test IP blacklist functionality"""
        service = APISecurityService()

        ip = "192.168.1.100"

        # IP should be allowed initially
        assert service.is_ip_allowed(ip) is True

        # Add to blacklist
        service.add_to_blacklist(ip)

        # IP should now be blocked
        assert service.is_ip_allowed(ip) is False

    def test_ip_whitelist_precedence(self):
        """Test that whitelist takes precedence over blacklist"""
        service = APISecurityService()

        ip = "192.168.1.200"

        # Add to both lists
        service.add_to_blacklist(ip)
        service.add_to_whitelist(ip)

        # Should be allowed due to whitelist precedence
        assert service.is_ip_allowed(ip) is True


# ======================================================================================
# CONTRACT SERVICE TESTS
# ======================================================================================


class TestContractService:
    """اختبارات خدمة العقود - Contract service tests"""

    def test_schema_compilation(self):
        """Test OpenAPI schema compilation"""
        service = APIContractService()

        # Check that schemas were compiled
        assert len(service.schema_cache) > 0
        assert "base_Error" in service.schema_cache
        assert "base_Success" in service.schema_cache

    def test_request_validation_valid(self):
        """Test valid request validation"""
        service = APIContractService()

        # Valid request data
        data = {"data": {"name": "test", "value": 123}}

        is_valid, errors = service.validate_request(
            endpoint="/api/database/record/users", method="POST", data=data
        )

        assert is_valid is True
        assert errors is None

    def test_request_validation_invalid(self):
        """Test invalid request validation"""
        service = APIContractService()

        # Invalid request data (missing required field)
        data = {"wrong_field": "value"}

        is_valid, errors = service.validate_request(
            endpoint="/api/database/record/users", method="POST", data=data
        )

        assert is_valid is False
        assert errors is not None

    def test_response_validation_success(self):
        """Test success response validation"""
        service = APIContractService()

        # Valid success response
        data = {"status": "success", "data": {"id": 1, "name": "test"}}

        is_valid, errors = service.validate_response(
            endpoint="/api/database/tables", method="GET", status_code=200, data=data
        )

        assert is_valid is True
        assert errors is None

    def test_response_validation_error(self):
        """Test error response validation"""
        service = APIContractService()

        # Valid error response
        data = {"status": "error", "error": "NotFound", "message": "Resource not found"}

        is_valid, errors = service.validate_response(
            endpoint="/api/database/record/users/999", method="GET", status_code=404, data=data
        )

        assert is_valid is True
        assert errors is None

    def test_endpoint_normalization(self):
        """Test endpoint path normalization"""
        service = APIContractService()

        # Test with numeric ID
        normalized = service._normalize_endpoint("/api/database/record/users/123")
        assert normalized == "/api/database/record/users/{id}"

        # Test with UUID
        normalized = service._normalize_endpoint("/api/database/record/tasks/abc-123-def")
        assert normalized == "/api/database/record/tasks/{id}"

    def test_openapi_spec_generation(self):
        """Test OpenAPI 3.0 specification generation"""
        service = APIContractService()

        spec = service.generate_openapi_spec()

        assert spec["openapi"] == "3.0.3"
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        assert "security" in spec

        # Check security schemes
        assert "BearerAuth" in spec["components"]["securitySchemes"]
        assert "RequestSignature" in spec["components"]["securitySchemes"]

    def test_contract_violation_logging(self):
        """Test contract violation tracking"""
        service = APIContractService()

        # Trigger a validation error
        data = {"invalid": "data"}
        service.validate_request(endpoint="/api/database/record/users", method="POST", data=data)

        # Check that violation was logged
        violations = service.get_contract_violations()
        assert len(violations) > 0

        # Check violation details
        violation = violations[0]
        assert violation["violation_type"] == "schema"
        assert violation["severity"] == "high"


# ======================================================================================
# INTEGRATION TESTS
# ======================================================================================


class TestIntegration:
    """اختبارات التكامل - Integration tests"""

    def test_observability_with_security(self):
        """Test observability and security working together"""
        obs_service = APIObservabilityService()
        sec_service = APISecurityService()

        # Generate token
        token = sec_service.generate_access_token(user_id=1)

        # Record metric
        obs_service.record_request_metrics(
            endpoint="/api/secure", method="GET", status_code=200, duration_ms=15.0, user_id=1
        )

        # Check both services recorded data
        snapshot = obs_service.get_performance_snapshot()
        assert snapshot.avg_latency_ms > 0

        payload = sec_service.verify_token(token.token)
        assert payload["user_id"] == 1

    def test_full_request_lifecycle(self):
        """Test complete request lifecycle with all services"""
        obs_service = APIObservabilityService()
        sec_service = APISecurityService()
        contract_service = APIContractService()

        client_id = "integration-test"

        # 1. Check rate limit
        allowed, _ = sec_service.check_rate_limit(client_id)
        assert allowed is True

        # 2. Validate request
        request_data = {"data": {"name": "test"}}
        is_valid, _ = contract_service.validate_request(
            endpoint="/api/database/record/users", method="POST", data=request_data
        )
        assert is_valid is True

        # 3. Record metrics
        obs_service.record_request_metrics(
            endpoint="/api/database/record/users", method="POST", status_code=200, duration_ms=18.5
        )

        # 4. Check SLA compliance
        compliance = obs_service.get_sla_compliance()
        assert compliance["sla_status"] == "compliant"
