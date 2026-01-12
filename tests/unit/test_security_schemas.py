from app.api.routers.security import UserResponse


def test_user_response_strictness():
    """
    Verify that UserResponse strictly filters out sensitive fields.
    """
    # Simulate data coming from service/database with sensitive fields
    internal_data = {
        "id": 1,
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "secret_hash_that_should_not_leak",
        "is_admin": False,
        "internal_metadata": {"foo": "bar"},
    }

    # Pydantic v2 model creation
    response_model = UserResponse.model_validate(internal_data)

    # Convert to dict
    output = response_model.model_dump()

    # Assertions
    assert output["id"] == 1
    assert output["name"] == "Test User"  # Check aliasing
    assert output["email"] == "test@example.com"

    # CRITICAL: Ensure sensitive fields are GONE
    assert "hashed_password" not in output
    assert "internal_metadata" not in output
    # Also ensure original alias key is not present unless configured to be populated
    assert "full_name" not in output  # Should be 'name' in output due to aliasing rules in dump?
    # Wait, model_dump(by_alias=True) would use alias. default is field name.
    # The field is defined as `name: str = Field(..., alias="full_name")`
    # default dump uses field name 'name'.
