"""Unit tests for Pydantic schemas and domain utilities."""
import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock
from app.api.schemas.admin import ChatRequest, ConversationSummaryResponse, MessageResponse
from app.api.schemas.ums import ProfileUpdateRequest
from app.core.domain.common import utc_now, CaseInsensitiveEnum, FlexibleEnum, JSONText
from app.core.domain.user import User, UserStatus, RefreshToken, PasswordResetToken
from pydantic import ValidationError
import enum


class TestUtcNow:
    def test_returns_utc_datetime(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == UTC


class TestCaseInsensitiveEnum:
    class SampleEnum(CaseInsensitiveEnum):
        ACTIVE = "active"
        PENDING = "pending"
    
    def test_match_uppercase_key(self):
        result = self.SampleEnum._missing_("ACTIVE")
        assert result == self.SampleEnum.ACTIVE
    
    def test_match_lowercase_value(self):
        result = self.SampleEnum._missing_("pending")
        assert result == self.SampleEnum.PENDING
    
    def test_no_match_returns_none(self):
        result = self.SampleEnum._missing_("unknown")
        assert result is None
    
    def test_non_string_returns_none(self):
        result = self.SampleEnum._missing_(123)
        assert result is None


class TestFlexibleEnum:
    class SampleEnum(enum.Enum):
        ACTIVE = "active"
    
    def test_bind_none(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_bind_param(None, MagicMock()) is None
    
    def test_bind_enum_value(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_bind_param(self.SampleEnum.ACTIVE, MagicMock()) == "active"
    
    def test_bind_string_value(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_bind_param("active", MagicMock()) == "active"
    
    def test_bind_invalid_string(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_bind_param("UNKNOWN", MagicMock()) == "unknown"
    
    def test_result_none(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_result_value(None, MagicMock()) is None
    
    def test_result_enum(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_result_value(self.SampleEnum.ACTIVE, MagicMock()) == self.SampleEnum.ACTIVE
    
    def test_result_string_match(self):
        fe = FlexibleEnum(self.SampleEnum)
        assert fe.process_result_value("active", MagicMock()) == self.SampleEnum.ACTIVE
    
    def test_result_fallback(self):
        fe = FlexibleEnum(self.SampleEnum)
        result = fe.process_result_value("unknown_value", MagicMock())
        assert result == "unknown_value"


class TestJSONText:
    def test_bind_none(self):
        jt = JSONText()
        assert jt.process_bind_param(None, MagicMock()) is None
    
    def test_bind_dict(self):
        jt = JSONText()
        assert jt.process_bind_param({"key": "value"}, MagicMock()) == '{"key": "value"}'
    
    def test_result_none(self):
        jt = JSONText()
        assert jt.process_result_value(None, MagicMock()) is None
    
    def test_result_valid_json(self):
        jt = JSONText()
        assert jt.process_result_value('{"key": "value"}', MagicMock()) == {"key": "value"}
    
    def test_result_invalid_json(self):
        jt = JSONText()
        assert jt.process_result_value("not json", MagicMock()) == "not json"


class TestChatRequest:
    def test_valid_question(self):
        req = ChatRequest(question="Hello world")
        assert req.question == "Hello world"
    
    def test_empty_question_fails(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="   ")
    
    def test_question_trimmed(self):
        req = ChatRequest(question="  padded  ")
        assert req.question == "padded"


class TestConversationSummaryResponse:
    def test_sync_identifiers_from_id(self):
        resp = ConversationSummaryResponse(id=123)
        assert resp.id == 123
        assert resp.conversation_id == 123
    
    def test_sync_identifiers_from_conversation_id(self):
        resp = ConversationSummaryResponse(id=0, conversation_id=456)
        assert resp.id == 456
        assert resp.conversation_id == 456


class TestProfileUpdateRequest:
    def test_empty_update_fails(self):
        with pytest.raises(ValidationError):
            ProfileUpdateRequest()
    
    def test_valid_email_update(self):
        req = ProfileUpdateRequest(email=" Test@Example.COM ")
        assert req.email == "test@example.com"


class TestUserModel:
    def test_set_and_check_password(self):
        user = User(full_name="Test", email="test@e.com")
        user.set_password("secret123")
        assert user.check_password("secret123") is True
        assert user.check_password("wrong") is False
    
    def test_check_password_no_hash(self):
        user = User(full_name="Test", email="test@e.com", password_hash=None)
        assert user.check_password("anything") is False
    
    def test_verify_password_alias(self):
        user = User(full_name="Test", email="test@e.com")
        user.set_password("secret")
        assert user.verify_password("secret") is True


class TestRefreshToken:
    def test_is_active_valid(self):
        token = RefreshToken(
            hashed_token="hash", 
            user_id=1, 
            expires_at=datetime(2099, 1, 1, tzinfo=UTC)
        )
        assert token.is_active() is True
    
    def test_is_active_expired(self):
        token = RefreshToken(
            hashed_token="hash", 
            user_id=1, 
            expires_at=datetime(2000, 1, 1, tzinfo=UTC)
        )
        assert token.is_active() is False
    
    def test_revoke(self):
        token = RefreshToken(
            hashed_token="hash", 
            user_id=1, 
            expires_at=datetime(2099, 1, 1, tzinfo=UTC)
        )
        token.revoke(replaced_by="new_id")
        assert token.revoked_at is not None
        assert token.replaced_by_token_id == "new_id"


class TestPasswordResetToken:
    def test_is_active_valid(self):
        token = PasswordResetToken(
            hashed_token="hash", 
            user_id=1, 
            expires_at=datetime(2099, 1, 1, tzinfo=UTC)
        )
        assert token.is_active() is True
    
    def test_mark_redeemed(self):
        token = PasswordResetToken(
            hashed_token="hash", 
            user_id=1, 
            expires_at=datetime(2099, 1, 1, tzinfo=UTC)
        )
        token.mark_redeemed()
        assert token.redeemed_at is not None
        assert token.is_active() is False
