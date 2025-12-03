from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.config.settings import AppSettings
from app.services.admin_chat_boundary_service import AdminChatBoundaryService


@pytest.mark.asyncio
async def test_admin_auth_uses_centralized_config():
    """
    Verifies that the AdminChatBoundaryService uses the SECRET_KEY from AppSettings
    instead of a hardcoded default or local env var.
    """
    # 1. Setup Mock Settings
    mock_secret = "dynamic-settings-secret-key"
    mock_settings = MagicMock(spec=AppSettings)
    mock_settings.SECRET_KEY = mock_secret

    # 2. Create a token signed with the SETTINGS key
    valid_token = jwt.encode({"sub": "123"}, mock_secret, algorithm="HS256")

    # 3. Create a token signed with the OLD default key (the bug)
    old_default_key = "your-super-secret-key"
    invalid_token = jwt.encode({"sub": "123"}, old_default_key, algorithm="HS256")

    # 4. Patch dependencies in app.services.admin_chat_boundary_service
    with (
        patch("app.services.admin_chat_boundary_service.get_settings", return_value=mock_settings),
        patch("app.services.admin_chat_boundary_service.get_service_boundary") as mock_get_service,
        patch("app.services.admin_chat_boundary_service.get_policy_boundary"),
    ):
        # Setup mock service boundary to avoid init failures
        mock_service_boundary = MagicMock()
        mock_get_service.return_value = mock_service_boundary

        # We need a mock DB session for the service init
        mock_db = MagicMock()

        # Instantiate the service. This calls get_settings() which is now mocked.
        service = AdminChatBoundaryService(db=mock_db)

        # Case A: Valid Token -> Should Return User ID
        auth_header_valid = f"Bearer {valid_token}"
        user_id = service.validate_auth_header(auth_header_valid)
        assert user_id == 123

        # Case B: Invalid Token -> Should Raise HTTPException
        auth_header_invalid = f"Bearer {invalid_token}"
        with pytest.raises(HTTPException) as exc_info:
            service.validate_auth_header(auth_header_invalid)
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail
