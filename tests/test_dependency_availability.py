import pytest

def test_import_api_contract_service():
    try:
        from app.services.api_contract_service import APIContractService
    except ImportError as e:
        pytest.fail(f"Failed to import APIContractService: {e}")
