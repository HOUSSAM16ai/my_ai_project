import pytest
from fastapi import HTTPException

from app.services.auth import OAuth2Provider


def test_oauth2_provider_flow():
    """اختبار تدفق OAuth2 الأساسي."""
    provider = OAuth2Provider()

    # 1. Register Client
    reg = provider.register_client(
        name="Test App", redirect_uris=["http://localhost/callback"], is_confidential=True
    )
    assert reg.client.client_id
    assert reg.client.client_secret_hash
    assert reg.raw_secret  # Must be returned!

    # 2. Validate Client
    # Should succeed with correct secret
    client = provider.validate_client(reg.client.client_id, reg.raw_secret)
    assert client.name == "Test App"

    # Should fail with wrong secret
    with pytest.raises(HTTPException):
        provider.validate_client(reg.client.client_id, "wrong_secret")

    # 3. Create Auth Code
    code = provider.create_authorization_code(
        client_id=reg.client.client_id,
        user_id="user_123",
        scope="read",
        redirect_uri="http://localhost/callback",
    )
    assert code

    # 4. Exchange Code
    token_data = provider.exchange_code_for_token(
        code=code, client_id=reg.client.client_id, redirect_uri="http://localhost/callback"
    )
    assert token_data["user_id"] == "user_123"
    assert token_data["scope"] == "read"
