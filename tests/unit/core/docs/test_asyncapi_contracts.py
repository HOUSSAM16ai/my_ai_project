from app.core.asyncapi_contracts import (
    default_asyncapi_contract_path,
    validate_asyncapi_contract_structure,
)


def test_asyncapi_contract_structure_is_valid():
    report = validate_asyncapi_contract_structure(default_asyncapi_contract_path())
    assert report.is_clean(), f"AsyncAPI contract errors: {report.errors}"
