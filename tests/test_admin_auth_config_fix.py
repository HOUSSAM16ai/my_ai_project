
import pytest
import sys
import os
import jwt
from unittest.mock import MagicMock, patch
from fastapi import Request, HTTPException

# We need to test the logic inside get_current_user_id specifically regarding key usage.
# Since we modified the code to use get_settings() at runtime (inside the function),
# we don't need to reload the module!
# My fix moved `settings = get_settings()` inside `get_current_user_id`.
# Wait, let me double check my fix.
# Yes:
#     token = parts[1]
#     settings = get_settings()
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

# This makes testing MUCH easier. We can just mock get_settings.

@pytest.mark.asyncio
async def test_admin_auth_uses_centralized_config():
    """
    Verifies that the admin router uses the SECRET_KEY from AppSettings
    instead of a hardcoded default or local env var.
    """
    from app.api.routers.admin import get_current_user_id
    from app.config.settings import AppSettings

    # 1. Setup Mock Settings
    mock_secret = "dynamic-settings-secret-key"
    mock_settings = MagicMock(spec=AppSettings)
    mock_settings.SECRET_KEY = mock_secret

    # 2. Create a token signed with the SETTINGS key
    valid_token = jwt.encode({"sub": "123"}, mock_secret, algorithm="HS256")

    # 3. Create a token signed with the OLD default key (the bug)
    old_default_key = "your-super-secret-key"
    invalid_token = jwt.encode({"sub": "123"}, old_default_key, algorithm="HS256")

    # 4. Mock Request
    req_valid = MagicMock(spec=Request)
    req_valid.headers = {"Authorization": f"Bearer {valid_token}"}

    req_invalid = MagicMock(spec=Request)
    req_invalid.headers = {"Authorization": f"Bearer {invalid_token}"}

    # 5. Patch get_settings to return our mock
    with patch("app.api.routers.admin.get_settings", return_value=mock_settings):

        # Case A: Valid Token (Signed with Settings Key) -> Should Succeed
        user_id = get_current_user_id(req_valid)
        assert user_id == 123

        # Case B: Invalid Token (Signed with Old Default) -> Should Fail
        # This proves we are NOT using the hardcoded default anymore.
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(req_invalid)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"
