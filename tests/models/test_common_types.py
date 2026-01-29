from datetime import UTC, datetime

from app.core.domain.common import FlexibleEnum, utc_now
from app.core.domain.models import JSONText, MessageRole

# =============================================================================
# UTC NOW HELPER TESTS
# =============================================================================


class TestUtcNow:
    """Tests for the utc_now helper function."""

    def test_returns_datetime(self):
        """utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_returns_utc_timezone(self):
        """utc_now returns datetime with UTC timezone."""
        result = utc_now()
        assert result.tzinfo == UTC

    def test_returns_current_time(self):
        """utc_now returns approximately current time."""
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)
        assert before <= result <= after


# =============================================================================
# CASE INSENSITIVE ENUM TESTS
# =============================================================================


class TestCaseInsensitiveEnum:
    """Tests for CaseInsensitiveEnum base class."""

    def test_lookup_by_uppercase_name(self):
        """Can lookup enum by uppercase name."""
        assert MessageRole["USER"] == MessageRole.USER
        assert MessageRole["ASSISTANT"] == MessageRole.ASSISTANT

    def test_lookup_by_lowercase_value(self):
        """Can lookup enum by lowercase value."""
        assert MessageRole("user") == MessageRole.USER
        assert MessageRole("assistant") == MessageRole.ASSISTANT

    def test_lookup_by_uppercase_value(self):
        """Can lookup enum by uppercase value via _missing_."""
        # The _missing_ method handles case conversion
        assert MessageRole("USER") == MessageRole.USER
        assert MessageRole("ASSISTANT") == MessageRole.ASSISTANT

    def test_lookup_by_mixed_case(self):
        """Can lookup enum by mixed case value."""
        assert MessageRole("User") == MessageRole.USER
        assert MessageRole("Assistant") == MessageRole.ASSISTANT

    def test_invalid_lookup_returns_none(self):
        """Invalid lookup returns None via _missing_."""
        result = MessageRole._missing_("invalid_value")
        assert result is None

    def test_non_string_lookup_returns_none(self):
        """Non-string lookup returns None."""
        result = MessageRole._missing_(123)
        assert result is None


# =============================================================================
# FLEXIBLE ENUM TYPE DECORATOR TESTS
# =============================================================================


class TestFlexibleEnum:
    """Tests for FlexibleEnum TypeDecorator."""

    def test_process_bind_param_with_enum(self):
        """Binding an enum stores its value."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param(MessageRole.USER, None)
        assert result == "user"

    def test_process_bind_param_with_string(self):
        """Binding a string normalizes to enum value."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param("USER", None)
        assert result == "user"

    def test_process_bind_param_with_none(self):
        """Binding None returns None."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param(None, None)
        assert result is None

    def test_process_result_value_returns_enum(self):
        """Result value is converted to enum."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value("user", None)
        assert result == MessageRole.USER

    def test_process_result_value_case_insensitive(self):
        """Result value handles case insensitively."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value("USER", None)
        assert result == MessageRole.USER

    def test_process_result_value_with_none(self):
        """Result value None returns None."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value(None, None)
        assert result is None


# =============================================================================
# JSON TEXT TYPE DECORATOR TESTS
# =============================================================================


class TestJSONText:
    """Tests for JSONText TypeDecorator."""

    def test_process_bind_param_with_dict(self):
        """Binding a dict serializes to JSON string."""
        decorator = JSONText()
        data = {"key": "value", "number": 42}
        result = decorator.process_bind_param(data, None)
        assert result == '{"key": "value", "number": 42}'

    def test_process_bind_param_with_list(self):
        """Binding a list serializes to JSON string."""
        decorator = JSONText()
        data = [1, 2, 3, "four"]
        result = decorator.process_bind_param(data, None)
        assert result == '[1, 2, 3, "four"]'

    def test_process_bind_param_with_none(self):
        """Binding None returns None."""
        decorator = JSONText()
        result = decorator.process_bind_param(None, None)
        assert result is None

    def test_process_bind_param_with_primitive(self):
        """Binding primitives serializes correctly."""
        decorator = JSONText()
        assert decorator.process_bind_param(42, None) == "42"
        assert decorator.process_bind_param(True, None) == "true"
        assert decorator.process_bind_param("string", None) == '"string"'

    def test_process_result_value_with_dict(self):
        """Result value deserializes dict from JSON."""
        decorator = JSONText()
        result = decorator.process_result_value('{"key": "value"}', None)
        assert result == {"key": "value"}

    def test_process_result_value_with_list(self):
        """Result value deserializes list from JSON."""
        decorator = JSONText()
        result = decorator.process_result_value("[1, 2, 3]", None)
        assert result == [1, 2, 3]

    def test_process_result_value_with_none(self):
        """Result value None returns None."""
        decorator = JSONText()
        result = decorator.process_result_value(None, None)
        assert result is None

    def test_process_result_value_with_invalid_json(self):
        """Result value returns raw value on JSON decode error."""
        decorator = JSONText()
        result = decorator.process_result_value("not valid json {", None)
        assert result == "not valid json {"

    def test_roundtrip_complex_data(self):
        """Complex data survives roundtrip through JSONText."""
        decorator = JSONText()
        data = {
            "nested": {"a": 1, "b": [2, 3]},
            "array": [{"x": 1}, {"y": 2}],
            "null": None,
            "bool": True,
        }
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data


# =============================================================================
# JSONTEXT EDGE CASES
# =============================================================================


class TestJSONTextEdgeCases:
    """Edge case tests for JSONText TypeDecorator."""

    def test_empty_dict(self):
        """Empty dict survives roundtrip."""
        decorator = JSONText()
        serialized = decorator.process_bind_param({}, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == {}

    def test_empty_list(self):
        """Empty list survives roundtrip."""
        decorator = JSONText()
        serialized = decorator.process_bind_param([], None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == []

    def test_unicode_in_json(self):
        """Unicode data survives roundtrip."""
        decorator = JSONText()
        data = {"arabic": "مرحبا", "emoji": "🚀", "chinese": "你好"}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data

    def test_nested_null_values(self):
        """Nested null values survive roundtrip."""
        decorator = JSONText()
        data = {"a": None, "b": {"c": None}}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data

    def test_large_json(self):
        """Large JSON data survives roundtrip."""
        decorator = JSONText()
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data
        assert len(deserialized["items"]) == 1000
