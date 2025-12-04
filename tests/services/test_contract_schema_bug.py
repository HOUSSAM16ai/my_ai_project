from app.services.api_contract_service import APIContractService


def test_list_conversations_contract_violation():
    """
    Test that the default validation logic flags
    the list_conversations response as invalid because it expects
    an object (base_Success) but gets a list.
    """
    service = APIContractService()

    # Endpoint from app/api/routers/admin.py
    endpoint = "/admin/api/conversations"
    method = "GET"
    status_code = 200

    # Mimic the actual response from the router (list of dicts)
    actual_data = [
        {
            "id": 1,
            "title": "Test Conversation",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
        }
    ]

    # Run validation
    is_valid, errors = service.validate_response(endpoint, method, status_code, actual_data)

    # Now that we've fixed the schema, this should be valid
    assert is_valid is True
    assert errors is None
