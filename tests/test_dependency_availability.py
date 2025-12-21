# tests/test_dependency_availability.py


def test_import_api_contract_service():
    from app.services.api.api_contract_service import APIContractService

    assert APIContractService is not None
