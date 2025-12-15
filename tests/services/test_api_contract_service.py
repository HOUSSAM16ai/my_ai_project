# tests/services/test_api_contract_service.py
import pytest
from app.services.api_contract_service import APIContractService, _service
from app.services.api_contract.domain.models import ContractValidationResult, ContractSchema


def test_singleton():
    """Test that the contract_service is a singleton instance via the facade"""
    from app.services.api_contract import get_api_contract_service
    instance1 = get_api_contract_service()
    instance2 = get_api_contract_service()
    assert instance1 is instance2


def test_validate_data_valid():
    """Test validating valid data against a contract"""
    service = APIContractService()
    contract_name = "test_contract"
    version = "v1"
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}

    # Register first
    service.register_contract(contract_name, version, schema)

    data = {"name": "test"}
    result = service.validate_data(contract_name, version, data)
    assert result.is_valid
    assert not result.errors


def test_validate_data_invalid():
    """Test validating invalid data"""
    service = APIContractService()
    contract_name = "test_contract"
    version = "v1"
    # Schema already registered in previous test if running in same process, but let's re-register or use unique name
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    service.register_contract(contract_name, version, schema)

    data = {"name": 123} # Invalid type
    result = service.validate_data(contract_name, version, data)
    assert not result.is_valid
    assert result.errors is not None


def test_get_active_versions():
    """Test getting active versions"""
    service = APIContractService()
    # Mocking the internal service response would be ideal, but for now we check it returns a list
    versions = service.get_active_versions()
    assert isinstance(versions, list)


def test_check_version_status():
    """Test checking version status"""
    service = APIContractService()
    status = service.check_version_status("v1")
    assert isinstance(status, str)
