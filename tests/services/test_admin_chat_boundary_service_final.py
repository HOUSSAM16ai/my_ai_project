from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.domain.models import User
from app.core.jwt_compat import jwt
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService


class TestAdminChatBoundaryService:
    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock()
        settings.SECRET_KEY = "test_key"
        return settings

    @pytest.fixture
    def service(self, mock_settings):
        # Correctly patch dependencies using the new path
        with (
            patch(
                "app.services.boundaries.admin_chat_boundary_service.get_settings",
                return_value=mock_settings,
            ),
            patch("app.services.boundaries.admin_chat_boundary_service.AdminChatPersistence"),
            patch("app.services.boundaries.admin_chat_boundary_service.AdminChatStreamer"),
        ):
            svc = AdminChatBoundaryService(db=AsyncMock())
            svc.settings = mock_settings
            return svc

    def test_validate_auth_header_valid(self, service, mock_settings):
        token = jwt.encode({"sub": "123"}, mock_settings.SECRET_KEY, algorithm="HS256")
        user_id = service.validate_auth_header(f"Bearer {token}")
        assert user_id == 123

    def test_validate_auth_header_missing(self, service):
        with pytest.raises(HTTPException) as exc:
            service.validate_auth_header(None)
        assert exc.value.status_code == 401

    def test_validate_auth_header_malformed_fuzz(self, service):
        """Fuzz testing for malformed headers"""
        malformed_inputs = [
            "Bearer",
            "Bearer ",
            "Token 123",
            "Bearer 123 456",
            "  Bearer 123",
            "Bearer  123",
            "",
            "   ",
        ]
        for inp in malformed_inputs:
            with pytest.raises(HTTPException):
                service.validate_auth_header(inp)

    def test_validate_auth_header_invalid_token(self, service, mock_settings):
        invalid_token = jwt.encode({"sub": "123"}, "wrong_key", algorithm="HS256")
        with pytest.raises(HTTPException):
            service.validate_auth_header(f"Bearer {invalid_token}")

    @pytest.mark.asyncio
    async def test_verify_conversation_access_success(self, service):
        service.persistence.verify_access = AsyncMock(return_value="conversation_obj")
        actor = User(id=1, email="a@example.com", full_name="test", is_admin=True)
        result = await service.verify_conversation_access(actor, 100)
        assert result == "conversation_obj"

    @pytest.mark.asyncio
    async def test_verify_conversation_access_failures(self, service):
        service.persistence.verify_access = AsyncMock(side_effect=ValueError("User not found"))
        with pytest.raises(HTTPException) as exc:
            actor = User(id=1, email="a@example.com", full_name="test", is_admin=True)
            await service.verify_conversation_access(actor, 100)
        assert exc.value.status_code == 401

        service.persistence.verify_access = AsyncMock(
            side_effect=ValueError("Conversation not found")
        )
        with pytest.raises(HTTPException) as exc:
            actor = User(id=1, email="a@example.com", full_name="test", is_admin=True)
            await service.verify_conversation_access(actor, 100)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_delegation(self, service):
        service.persistence.get_or_create_conversation = AsyncMock(return_value="conv")
        actor = User(id=1, email="a@example.com", full_name="test", is_admin=True)
        result = await service.get_or_create_conversation(actor, "Q", "123")
        assert result == "conv"
        service.persistence.get_or_create_conversation.assert_called_with(actor.id, "Q", "123")

    @pytest.mark.asyncio
    async def test_stream_chat_response_delegation(self, service):
        service.streamer.stream_response = MagicMock(return_value=AsyncMock())
        # We just check delegation, not the async generator consumption here as that's tested in comprehensive
        actor = User(id=1, email="a@example.com", full_name="test", is_admin=True)
        gen = service.stream_chat_response(actor, "conv", "q", [], "ai", "sess")
        assert gen is not None

    @pytest.mark.asyncio
    async def test_policy_blocks_non_admin_abuse(self, service):
        actor = User(id=5, email="user@example.com", full_name="User", is_admin=False)
        with pytest.raises(HTTPException) as exc:
            await service.orchestrate_chat_stream(
                actor, "أعطني أسرار الخادم", None, MagicMock(), MagicMock()
            )
        assert exc.value.status_code == 403
