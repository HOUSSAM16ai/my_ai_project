"""
Comprehensive Tests for FlexibleEnum
════════════════════════════════════
"""

import pytest
from app.core.enum_types import FlexibleEnum
from app.models import MessageRole


class TestFlexibleEnum:
    """Test suite for FlexibleEnum TypeDecorator"""

    @pytest.fixture
    def enum_type(self):
        return FlexibleEnum(MessageRole)

    # ─────────────────────────────────────────────────────
    # Write Tests (process_bind_param)
    # ─────────────────────────────────────────────────────

    def test_bind_enum_member(self, enum_type):
        """Enum member → lowercase string"""
        result = enum_type.process_bind_param(MessageRole.USER, None)
        assert result == "user"

    def test_bind_uppercase_string(self, enum_type):
        """'USER' → 'user'"""
        result = enum_type.process_bind_param("USER", None)
        assert result == "user"

    def test_bind_lowercase_string(self, enum_type):
        """'user' → 'user'"""
        result = enum_type.process_bind_param("user", None)
        assert result == "user"

    def test_bind_none(self, enum_type):
        """None → None"""
        result = enum_type.process_bind_param(None, None)
        assert result is None

    # ─────────────────────────────────────────────────────
    # Read Tests (process_result_value)
    # ─────────────────────────────────────────────────────

    def test_result_lowercase(self, enum_type):
        """'user' → MessageRole.USER"""
        result = enum_type.process_result_value("user", None)
        assert result == MessageRole.USER

    def test_result_uppercase(self, enum_type):
        """'USER' → MessageRole.USER (legacy support)"""
        result = enum_type.process_result_value("USER", None)
        assert result == MessageRole.USER

    def test_result_mixed_case(self, enum_type):
        """'User' → MessageRole.USER"""
        result = enum_type.process_result_value("User", None)
        assert result == MessageRole.USER

    def test_result_none(self, enum_type):
        """None → None"""
        result = enum_type.process_result_value(None, None)
        assert result is None

    def test_result_invalid_raises(self, enum_type):
        """'INVALID' → ValueError"""
        with pytest.raises(ValueError, match="Cannot convert"):
            enum_type.process_result_value("INVALID", None)

    # ─────────────────────────────────────────────────────
    # Roundtrip Tests for All Values
    # ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("role", list(MessageRole))
    def test_roundtrip_all_roles(self, enum_type, role):
        """All values survive write→read"""
        written = enum_type.process_bind_param(role, None)
        read = enum_type.process_result_value(written, None)
        assert read == role

    @pytest.mark.parametrize("role", list(MessageRole))
    def test_uppercase_legacy_read(self, enum_type, role):
        """Reading legacy uppercase data"""
        uppercase = role.name.upper()
        result = enum_type.process_result_value(uppercase, None)
        assert result == role

    # ─────────────────────────────────────────────────────
    # Caching Tests
    # ─────────────────────────────────────────────────────

    def test_cache_hit(self, enum_type):
        """Verify cache operation"""
        # First call
        enum_type._resolve_enum("user")

        # Check cache stats
        info = enum_type._resolve_enum.cache_info()
        assert info.hits >= 0

        # Second call (should hit cache)
        enum_type._resolve_enum("user")
        new_info = enum_type._resolve_enum.cache_info()
        assert new_info.hits > info.hits
