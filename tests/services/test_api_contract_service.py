# tests/services/test_api_contract_service.py
from app.services.api_contract_service import APIContractService, contract_service


def test_singleton():
    """Test that the contract_service is a singleton instance"""
    from app.services.api_contract_service import contract_service as instance1
    from app.services.api_contract_service import contract_service as instance2
    assert instance1 is instance2


def test_validate_valid_request():
    """Test validating a valid request"""
    service = APIContractService()
    endpoint = "/api/database/record/my_table"
    method = "POST"
    data = {"data": {"name": "test"}}
    is_valid, errors = service.validate_request(endpoint, method, data)
    assert is_valid
    assert errors is None


def test_validate_invalid_request():
    """Test validating an invalid request"""
    service = APIContractService()
    endpoint = "/api/database/record/my_table"
    method = "POST"
    data = {"wrong_key": "test"}
    is_valid, errors = service.validate_request(endpoint, method, data)
    assert not is_valid
    assert errors is not None


def test_validate_valid_response():
    """Test validating a valid response"""
    service = APIContractService()
    endpoint = "/api/database/health"
    method = "GET"
    status_code = 200
    data = {
        "status": "healthy",
        "timestamp": "2025-01-01T00:00:00Z",
        "checks": {},
    }
    is_valid, errors = service.validate_response(endpoint, method, status_code, data)
    assert is_valid
    assert errors is None


def test_validate_invalid_response():
    """Test validating an invalid response"""
    service = APIContractService()
    endpoint = "/api/database/health"
    method = "GET"
    status_code = 200
    data = {"status": "invalid"}
    is_valid, errors = service.validate_response(endpoint, method, status_code, data)
    assert not is_valid
    assert errors is not None


def test_get_api_version_from_header():
    """Test getting API version from header"""
    service = APIContractService()
    headers = {"X-API-Version": "v1"}
    path = "/some/path"
    version = service.get_api_version(headers, path)
    assert version == "v1"


def test_get_api_version_from_path():
    """Test getting API version from path"""
    service = APIContractService()
    headers = {}
    path = "/v1/some/path"
    version = service.get_api_version(headers, path)
    assert version == "v1"


def test_get_default_api_version():
    """Test getting the default API version"""
    service = APIContractService()
    headers = {}
    path = "/some/path"
    version = service.get_api_version(headers, path)
    assert version == "v2"


def test_check_version_compatibility():
    """Test checking version compatibility"""
    service = APIContractService()
    headers = {"X-API-Version": "v1"}
    path = "/some/path"
    assert service.check_version_compatibility("/ep", "GET", headers, path)


def test_log_contract_violation():
    """Test logging a contract violation"""
    service = APIContractService()
    assert len(service.contract_violations) == 0
    service._log_contract_violation(
        endpoint="/test",
        method="GET",
        violation_type="schema",
        severity="critical",
        details={},
    )
    assert len(service.contract_violations) == 1


def test_get_contract_violations():
    """Test getting contract violations"""
    service = APIContractService()
    service._log_contract_violation(
        endpoint="/test",
        method="GET",
        violation_type="schema",
        severity="critical",
        details={},
    )
    violations = service.get_contract_violations()
    assert len(violations) == 1
    assert violations[0]["endpoint"] == "/test"


def test_generate_openapi_spec():
    """Test generating OpenAPI spec"""
    service = APIContractService()
    spec = service.generate_openapi_spec()
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec
