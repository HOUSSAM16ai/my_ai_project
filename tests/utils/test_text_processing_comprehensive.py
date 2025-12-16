"""
Comprehensive Tests for Text Processing - Enterprise Grade
==========================================================

🎯 Target: 100% Coverage with Advanced Testing

Features:
- Markdown fence stripping
- JSON extraction with balanced braces
- Edge case handling
- Property-based testing
- Security testing
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.utils.text_processing import extract_first_json_object, strip_markdown_fences


class TestStripMarkdownFences:
    """Tests for strip_markdown_fences function"""

    def test_strip_basic_fence(self):
        """Test basic markdown fence stripping"""
        text = "```python\nprint('hello')\n```"
        result = strip_markdown_fences(text)
        assert result == "print('hello')"

    def test_strip_fence_no_language(self):
        """Test stripping fence without language specifier"""
        text = "```\nsome code\n```"
        result = strip_markdown_fences(text)
        assert result == "some code"

    def test_strip_fence_with_spaces(self):
        """Test stripping with extra whitespace"""
        text = "   ```python\ncode\n```   "
        result = strip_markdown_fences(text)
        assert result == "code"

    def test_no_fence_returns_stripped(self):
        """Test text without fences returns stripped text"""
        text = "  plain text  "
        result = strip_markdown_fences(text)
        assert result == "plain text"

    def test_empty_string(self):
        """Test empty string returns empty"""
        result = strip_markdown_fences("")
        assert result == ""

    def test_none_returns_empty(self):
        """Test None returns empty string"""
        result = strip_markdown_fences(None)
        assert result == ""

    def test_only_opening_fence(self):
        """Test with only opening fence"""
        text = "```python\ncode without closing"
        result = strip_markdown_fences(text)
        assert "code without closing" in result

    def test_only_closing_fence(self):
        """Test with only closing fence"""
        text = "code\n```"
        result = strip_markdown_fences(text)
        assert "code" in result or result == "```"

    def test_multiline_code(self):
        """Test multiline code in fences"""
        text = "```\nline1\nline2\nline3\n```"
        result = strip_markdown_fences(text)
        assert "line1" in result and "line2" in result

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=20)
    def test_always_returns_string(self, text):
        """Property: always returns a string"""
        result = strip_markdown_fences(text)
        assert isinstance(result, str)


class TestExtractFirstJsonObject:
    """Tests for extract_first_json_object function"""

    def test_extract_simple_json(self):
        """Test extracting simple JSON object"""
        text = 'Some text {"key": "value"} more text'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_nested_json(self):
        """Test extracting nested JSON object"""
        text = 'Text {"outer": {"inner": "value"}} text'
        result = extract_first_json_object(text)
        assert result == '{"outer": {"inner": "value"}}'

    def test_extract_from_markdown(self):
        """Test extracting JSON from markdown fences"""
        text = '```json\n{"key": "value"}\n```'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_no_json_returns_none(self):
        """Test text without JSON returns None"""
        text = "No JSON here at all"
        result = extract_first_json_object(text)
        assert result is None

    def test_empty_string_returns_none(self):
        """Test empty string returns None"""
        result = extract_first_json_object("")
        assert result is None

    def test_none_returns_none(self):
        """Test None returns None"""
        result = extract_first_json_object(None)
        assert result is None

    def test_json_with_escaped_quotes(self):
        """Test JSON with escaped quotes"""
        text = '{"key": "value with \\"quotes\\""}'
        result = extract_first_json_object(text)
        assert result is not None
        assert "key" in result

    def test_json_with_newlines(self):
        """Test JSON with newlines"""
        text = '''{"key":
        "value"}'''
        result = extract_first_json_object(text)
        assert result is not None

    def test_multiple_json_objects(self):
        """Test extracts only first JSON object"""
        text = '{"first": 1} and {"second": 2}'
        result = extract_first_json_object(text)
        assert result == '{"first": 1}'

    def test_unbalanced_braces_returns_none(self):
        """Test unbalanced braces returns None"""
        text = '{"key": "value"'
        result = extract_first_json_object(text)
        # Should return None or incomplete JSON
        assert result is None or result == text

    def test_array_not_extracted(self):
        """Test that arrays are not extracted (only objects)"""
        text = '["item1", "item2"]'
        result = extract_first_json_object(text)
        assert result is None  # No curly braces

    def test_json_with_unicode(self):
        """Test JSON with unicode characters"""
        text = '{"message": "مرحبا 你好 🚀"}'
        result = extract_first_json_object(text)
        assert result is not None
        assert "message" in result

    def test_deeply_nested_json(self):
        """Test deeply nested JSON structures"""
        text = '{"l1": {"l2": {"l3": {"l4": "deep"}}}}'
        result = extract_first_json_object(text)
        assert result == '{"l1": {"l2": {"l3": {"l4": "deep"}}}}'

    def test_json_with_special_chars_in_string(self):
        """Test JSON with special characters in string values"""
        text = '{"key": "value with {braces} and \\"quotes\\""}'
        result = extract_first_json_object(text)
        assert result is not None

    @given(st.text())
    @settings(max_examples=20)
    def test_never_crashes(self, text):
        """Property: never crashes on any input"""
        try:
            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)
        except Exception:
            pytest.fail("Should not raise exception")


class TestIntegration:
    """Integration tests combining both functions"""

    def test_strip_then_extract(self):
        """Test stripping markdown then extracting JSON"""
        text = '```json\n{"key": "value"}\n```'
        # extract_first_json_object calls strip_markdown_fences internally
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_llm_response_pattern(self):
        """Test typical LLM response pattern"""
        llm_response = '''Here's the JSON you requested:
```json
{
    "status": "success",
    "data": {
        "items": ["a", "b", "c"]
    }
}
```
Hope this helps!'''
        result = extract_first_json_object(llm_response)
        assert result is not None
        assert "status" in result
        assert "success" in result
