# tests/test_services_standalone.py
# ======================================================================================
# ==      STANDALONE TESTS FOR WORLD-CLASS SERVICES (NO FLASK APP REQUIRED)        ==
# ======================================================================================


import pytest


# Test observability service directly without Flask context
def test_observability_service_import():
    """Test that observability service can be imported"""
    from app.services.api_observability_service import APIObservabilityService

    service = APIObservabilityService()
    assert service is not None
    assert service.sla_target_ms == 20.0


@pytest.mark.usefixtures("app_context")
def test_observability_metrics():
    """Test metrics recording without Flask"""
    from app.services.api_observability_service import APIObservabilityService

    service = APIObservabilityService()

    # Record some metrics
    service.record_request_metrics(
        endpoint="/api/test", method="GET", status_code=200, duration_ms=15.5, user_id=1
    )

    # Get snapshot
    snapshot = service.get_performance_snapshot()
    assert snapshot.avg_latency_ms > 0


def test_security_service_import():
    """Test that security service can be imported"""
    from app.services.api_security_service import APISecurityService

    service = APISecurityService()
    assert service is not None


def test_security_jwt_tokens():
    """Test JWT token generation"""
    from app.services.api_security_service import APISecurityService

    service = APISecurityService()
    token = service.generate_access_token(user_id=1, scopes=["read"])

    assert token is not None
    assert token.user_id == 1
    assert token.scopes == ["read"]


def test_contract_service_import():
    """Test that contract service can be imported"""
    from app.services.api_contract_service import APIContractService

    service = APIContractService()
    assert service is not None


def test_contract_openapi_spec():
    """Test OpenAPI specification generation"""
    from app.services.api_contract_service import APIContractService

    service = APIContractService()
    spec = service.generate_openapi_spec()

    assert spec["openapi"] == "3.0.3"
    assert "info" in spec
    assert "paths" in spec


@pytest.mark.usefixtures("app_context")
def test_all_services_integration():
    """Test that all services work together"""
    from app.services.api_contract_service import APIContractService
    from app.services.api_observability_service import APIObservabilityService
    from app.services.api_security_service import APISecurityService

    obs = APIObservabilityService()
    sec = APISecurityService()
    contract = APIContractService()

    # All services should be initialized
    assert obs is not None
    assert sec is not None
    assert contract is not None

    # Test basic functionality
    token = sec.generate_access_token(user_id=1)
    obs.record_request_metrics("/api/test", "GET", 200, 15.0)
    spec = contract.generate_openapi_spec()

    assert token.user_id == 1
    assert obs.get_performance_snapshot().avg_latency_ms > 0
    assert spec["openapi"] == "3.0.3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
