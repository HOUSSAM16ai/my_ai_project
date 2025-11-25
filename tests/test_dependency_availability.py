import pytest

# tests/test_dependency_availability.py

def test_import_api_contract_service():
    # Simulating check for optional dependency
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed")

    from app.services.api_contract_service import APIContractService
    assert APIContractService is not None
