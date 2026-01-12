from unittest.mock import MagicMock, patch

import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings


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

    # 4. Patch dependencies
    with (
        patch(
            "app.services.boundaries.admin_chat_boundary_service.get_settings",
            return_value=mock_settings,
        ),
        # We need to mock AdminChatPersistence because __init__ creates it
        patch("app.services.boundaries.admin_chat_boundary_service.AdminChatPersistence"),
        patch("app.services.boundaries.admin_chat_boundary_service.AdminChatStreamer"),
    ):
        from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService

        # Mock DB session for init
        mock_db = MagicMock(spec=AsyncSession)
        service = AdminChatBoundaryService(db=mock_db)

        # 5. Test Valid Token (Should Pass)
        try:
            result = service.validate_auth_header(f"Bearer {valid_token}")
            assert result == 123
        except Exception as e:
            pytest.fail(f"Service rejected token signed with AppSettings key: {e}")

        # 6. Test Invalid Token (Should Fail)
        try:
            service.validate_auth_header(f"Bearer {invalid_token}")
            pytest.fail("Service accepted token signed with OLD default key!")
        except Exception:
            # Expected failure
            pass
