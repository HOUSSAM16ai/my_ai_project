# tests/services/test_admin_chat_boundary_service_final.py
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from hypothesis import given
from hypothesis import strategies as st

from app.models import AdminConversation
from app.services.admin_chat_boundary_service import AdminChatBoundaryService
from tests.utils.unified_test_template import UnifiedTestTemplate


# === Test Class ===
class TestAdminChatBoundaryService(UnifiedTestTemplate):
    @pytest.fixture
    def mock_db_session(self):
        return self.async_mock()

    @pytest.fixture
    def mock_settings(self):
        mock = MagicMock()
        mock.SECRET_KEY = "super_secret_test_key"
        return mock

    @pytest.fixture
    def service(self, mock_db_session, mock_settings):
        # We need to mock the dependencies created in __init__
        with (
            patch(
                "app.services.admin_chat_boundary_service.get_settings", return_value=mock_settings
            ),
            patch("app.services.admin_chat_boundary_service.get_service_boundary") as mock_sb,
            patch("app.services.admin_chat_boundary_service.get_policy_boundary") as _mock_pb,
            patch(
                "app.services.admin_chat_boundary_service.AdminChatPersistence"
            ) as mock_persistence_cls,
            patch(
                "app.services.admin_chat_boundary_service.AdminChatStreamer"
            ) as mock_streamer_cls,
        ):
            # Setup mocks
            mock_sb.return_value.get_or_create_circuit_breaker = MagicMock()

            service = AdminChatBoundaryService(mock_db_session)

            # Attach mocks to service instance for assertion
            service.persistence = mock_persistence_cls.return_value
            service.streamer = mock_streamer_cls.return_value

            return service

    # --- Unit Tests: Auth Validation ---

    def test_validate_auth_header_valid(self, service, mock_settings):
        user_id = 123
        token = jwt.encode({"sub": str(user_id)}, mock_settings.SECRET_KEY, algorithm="HS256")
        header = f"Bearer {token}"
        result = service.validate_auth_header(header)
        assert result == user_id

    def test_validate_auth_header_missing(self, service):
        with pytest.raises(HTTPException) as exc:
            service.validate_auth_header(None)
        assert exc.value.status_code == 401

    @given(st.text())
    @UnifiedTestTemplate.HYPOTHESIS_SETTINGS
    def test_validate_auth_header_malformed_fuzz(self, service, random_header):
        if (
            random_header
            and len(random_header.split()) == 2
            and random_header.lower().startswith("bearer")
        ):
            pass
        with pytest.raises(HTTPException) as exc:
            service.validate_auth_header(random_header)
        assert exc.value.status_code == 401

    def test_validate_auth_header_invalid_token(self, service):
        with pytest.raises(HTTPException) as exc:
            service.validate_auth_header("Bearer invalidtoken123")
        assert exc.value.status_code == 401

    # --- Unit Tests: Conversation Access ---

    @pytest.mark.asyncio
    async def test_verify_conversation_access_success(self, service):
        expected_conv = AdminConversation(id=1, user_id=10, title="Test")
        service.persistence.verify_access = AsyncMock(return_value=expected_conv)
        result = await service.verify_conversation_access(10, 1)
        assert result == expected_conv

    @pytest.mark.asyncio
    async def test_verify_conversation_access_failures(self, service):
        service.persistence.verify_access = AsyncMock(side_effect=ValueError("User not found"))
        with pytest.raises(HTTPException) as exc:
            await service.verify_conversation_access(999, 1)
        assert exc.value.status_code == 401

    # --- Unit Tests: Get or Create Conversation ---

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_delegation(self, service):
        service.persistence.get_or_create_conversation = AsyncMock(return_value="mock_conv")
        res = await service.get_or_create_conversation(1, "Q", "cid")
        assert res == "mock_conv"

    # --- Unit Tests: Streaming ---

    @pytest.mark.asyncio
    async def test_stream_chat_response_delegation(self, service):
        async def mock_stream(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"

        service.streamer.stream_response = mock_stream
        chunks = []
        async for c in service.stream_chat_response(1, "conv", "q", [], "ai", "sess"):
            chunks.append(c)
        assert chunks == ["chunk1", "chunk2"]
