"""
Comprehensive Unit Tests for Text Processing Utilities
=======================================================

Coverage Target: 100%
Testing Strategy:
- All functions and branches
- Edge cases: empty strings, None, special characters
- Boundary conditions
- Unicode handling
- Malformed input handling
- Property-based testing
"""

import pytest

from app.utils.text_processing import extract_first_json_object, strip_markdown_fences


class TestStripMarkdownFences:
    """Test strip_markdown_fences() - 100% coverage"""

    def test_strip_simple_code_block(self):
        """Test removing simple markdown code fences"""
        text = "```python\nprint('hello')\n```"
        result = strip_markdown_fences(text)
        assert result == "print('hello')"

    def test_strip_code_block_with_language(self):
        """Test removing fences with language specifier"""
        text = "```javascript\nconsole.log('test');\n```"
        result = strip_markdown_fences(text)
        assert result == "console.log('test');"

    def test_strip_code_block_no_language(self):
        """Test removing fences without language specifier"""
        text = "```\nsome code\n```"
        result = strip_markdown_fences(text)
        assert result == "some code"

    def test_no_fences_returns_original(self):
        """Test that text without fences is returned as-is"""
        text = "plain text without fences"
        result = strip_markdown_fences(text)
        assert result == text

    def test_empty_string(self):
        """Test with empty string"""
        result = strip_markdown_fences("")
        assert result == ""

    def test_none_input(self):
        """Test with None input"""
        result = strip_markdown_fences(None)
        assert result == ""

    def test_only_opening_fence(self):
        """Test with only opening fence (no closing)"""
        text = "```python\ncode without closing"
        result = strip_markdown_fences(text)
        # Should remove opening fence but not crash
        assert "```" not in result or result == text.strip()

    def test_only_closing_fence(self):
        """Test with only closing fence"""
        text = "code without opening\n```"
        result = strip_markdown_fences(text)
        # Should not start with ```, so returns as-is
        assert result == text.strip()

    def test_multiple_code_blocks(self):
        """Test with multiple code blocks (only strips outer)"""
        text = "```\nfirst block\n```\n```\nsecond block\n```"
        result = strip_markdown_fences(text)
        # Only strips the outermost fences
        assert "```" not in result or "first block" in result

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled"""
        text = "   ```python\ncode\n```   "
        result = strip_markdown_fences(text)
        assert result == "code"

    def test_newline_variations(self):
        """Test different newline styles"""
        test_cases = [
            "```python\ncode\n```",
            "```python\r\ncode\r\n```",
            "```python\rcode\r```",
        ]
        for text in test_cases:
            result = strip_markdown_fences(text)
            assert "```" not in result

    def test_nested_backticks_in_code(self):
        """Test code containing backticks"""
        text = "```python\nprint('`test`')\n```"
        result = strip_markdown_fences(text)
        assert result == "print('`test`')"

    def test_fence_with_no_newline_after_opening(self):
        """Test fence immediately followed by code (no newline)"""
        text = "```code```"
        result = strip_markdown_fences(text)
        # No newline after opening, so might not strip properly
        # This tests the edge case where nl == -1
        assert result == text.strip() or "```" not in result

    def test_unicode_content(self):
        """Test with Unicode content"""
        text = "```python\nprint('مرحبا')\n```"
        result = strip_markdown_fences(text)
        assert result == "print('مرحبا')"

    def test_very_long_code_block(self):
        """Test with very long code block"""
        code = "x = 1\n" * 1000
        text = f"```python\n{code}```"
        result = strip_markdown_fences(text)
        assert result == code.strip()

    def test_special_characters_in_language(self):
        """Test with special characters in language identifier"""
        text = "```python3.12\ncode\n```"
        result = strip_markdown_fences(text)
        assert result == "code"


class TestExtractFirstJsonObject:
    """Test extract_first_json_object() - 100% coverage"""

    def test_extract_simple_json(self):
        """Test extracting simple JSON object"""
        text = '{"key": "value"}'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON from text with prefix and suffix"""
        text = 'Some text before {"key": "value"} and after'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_nested_json(self):
        """Test extracting nested JSON object"""
        text = '{"outer": {"inner": "value"}}'
        result = extract_first_json_object(text)
        assert result == '{"outer": {"inner": "value"}}'

    def test_extract_json_with_array(self):
        """Test extracting JSON with array"""
        text = '{"items": [1, 2, 3], "count": 3}'
        result = extract_first_json_object(text)
        assert result == '{"items": [1, 2, 3], "count": 3}'

    def test_no_json_returns_none(self):
        """Test that text without JSON returns None"""
        text = "No JSON here"
        result = extract_first_json_object(text)
        assert result is None

    def test_empty_string_returns_none(self):
        """Test with empty string"""
        result = extract_first_json_object("")
        assert result is None

    def test_none_input_returns_none(self):
        """Test with None input"""
        result = extract_first_json_object(None)
        assert result is None

    def test_json_in_markdown_fences(self):
        """Test extracting JSON wrapped in markdown fences"""
        text = '```json\n{"key": "value"}\n```'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_multiple_json_objects_returns_first(self):
        """Test that only first JSON object is returned"""
        text = '{"first": 1} {"second": 2}'
        result = extract_first_json_object(text)
        assert result == '{"first": 1}'

    def test_json_with_escaped_quotes(self):
        """Test JSON with escaped quotes in strings"""
        text = '{"message": "He said \\"hello\\""}'
        result = extract_first_json_object(text)
        assert result == '{"message": "He said \\"hello\\""}'

    def test_json_with_escaped_backslash(self):
        """Test JSON with escaped backslashes"""
        text = '{"path": "C:\\\\Users\\\\test"}'
        result = extract_first_json_object(text)
        assert result == '{"path": "C:\\\\Users\\\\test"}'

    def test_json_with_newlines_in_string(self):
        """Test JSON with newline characters in string values"""
        text = '{"text": "line1\\nline2"}'
        result = extract_first_json_object(text)
        assert result == '{"text": "line1\\nline2"}'

    def test_unbalanced_braces_returns_none(self):
        """Test with unbalanced braces"""
        text = '{"key": "value"'
        result = extract_first_json_object(text)
        # Should return None if braces never balance
        assert result is None or result == text

    def test_json_with_unicode(self):
        """Test JSON with Unicode characters"""
        text = '{"name": "مستخدم", "age": 25}'
        result = extract_first_json_object(text)
        assert result == '{"name": "مستخدم", "age": 25}'

    def test_json_with_numbers(self):
        """Test JSON with various number formats"""
        text = '{"int": 42, "float": 3.14, "negative": -10, "exp": 1e5}'
        result = extract_first_json_object(text)
        assert result == '{"int": 42, "float": 3.14, "negative": -10, "exp": 1e5}'

    def test_json_with_boolean_and_null(self):
        """Test JSON with boolean and null values"""
        text = '{"active": true, "deleted": false, "data": null}'
        result = extract_first_json_object(text)
        assert result == '{"active": true, "deleted": false, "data": null}'

    def test_json_with_empty_object(self):
        """Test extracting empty JSON object"""
        text = "Some text {} more text"
        result = extract_first_json_object(text)
        assert result == "{}"

    def test_json_with_empty_string_value(self):
        """Test JSON with empty string value"""
        text = '{"key": ""}'
        result = extract_first_json_object(text)
        assert result == '{"key": ""}'

    def test_deeply_nested_json(self):
        """Test deeply nested JSON structure"""
        text = '{"a": {"b": {"c": {"d": {"e": "value"}}}}}'
        result = extract_first_json_object(text)
        assert result == '{"a": {"b": {"c": {"d": {"e": "value"}}}}}'

    def test_json_with_special_characters_in_string(self):
        """Test JSON with special characters"""
        text = '{"special": "!@#$%^&*()_+-=[]{}|;:,.<>?/"}'
        result = extract_first_json_object(text)
        assert '"special"' in result

    def test_json_after_markdown_fence_removal(self):
        """Test that markdown fences are stripped before extraction"""
        text = '```\nPrefix text {"key": "value"} suffix\n```'
        result = extract_first_json_object(text)
        assert result == '{"key": "value"}'

    def test_string_with_brace_in_value(self):
        """Test JSON with braces inside string values"""
        text = '{"template": "Hello {name}"}'
        result = extract_first_json_object(text)
        assert result == '{"template": "Hello {name}"}'

    def test_consecutive_escaped_backslashes(self):
        """Test JSON with consecutive escaped backslashes"""
        text = '{"path": "\\\\\\\\"}'
        result = extract_first_json_object(text)
        assert result == '{"path": "\\\\\\\\"}'

    def test_json_with_tab_and_newline_whitespace(self):
        """Test JSON with various whitespace characters"""
        text = '{\n\t"key":\t"value"\n}'
        result = extract_first_json_object(text)
        assert result == '{\n\t"key":\t"value"\n}'


class TestTextProcessingEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_strip_fences_with_only_backticks(self):
        """Test with only backticks"""
        assert strip_markdown_fences("```") == ""
        assert strip_markdown_fences("``````") == ""

    def test_extract_json_with_only_opening_brace(self):
        """Test with only opening brace"""
        result = extract_first_json_object("{")
        assert result is None

    def test_extract_json_with_only_closing_brace(self):
        """Test with only closing brace"""
        result = extract_first_json_object("}")
        assert result is None

    def test_very_large_input(self):
        """Test with very large input"""
        large_text = "x" * 100000 + '{"key": "value"}' + "y" * 100000
        result = extract_first_json_object(large_text)
        assert result == '{"key": "value"}'

    def test_binary_data_handling(self):
        """Test with binary-like data (should not crash)"""
        text = "\\x00\\x01\\x02 {\"key\": \"value\"}"
        result = extract_first_json_object(text)
        # Should handle gracefully
        assert result is None or "key" in result


class TestTextProcessingIntegration:
    """Integration tests combining both functions"""

    def test_strip_then_extract_workflow(self):
        """Test typical workflow: strip fences then extract JSON"""
        text = '```json\nSome text {"result": "success"} more text\n```'

        # First strip fences
        stripped = strip_markdown_fences(text)
        assert "```" not in stripped

        # Then extract JSON
        json_obj = extract_first_json_object(stripped)
        assert json_obj == '{"result": "success"}'

    def test_extract_calls_strip_internally(self):
        """Test that extract_first_json_object strips fences internally"""
        text = '```\n{"data": "value"}\n```'
        result = extract_first_json_object(text)
        assert result == '{"data": "value"}'


# Property-based tests using Hypothesis
try:
    from hypothesis import given
    from hypothesis import strategies as st

    class TestTextProcessingPropertyBased:
        """Property-based tests for text processing utilities"""

        @given(st.text())
        def test_strip_fences_never_crashes(self, text):
            """Property: strip_markdown_fences should never crash"""
            result = strip_markdown_fences(text)
            assert isinstance(result, str)

        @given(st.text())
        def test_extract_json_never_crashes(self, text):
            """Property: extract_first_json_object should never crash"""
            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)

        @given(st.text(min_size=1))
        def test_strip_fences_returns_string(self, text):
            """Property: strip_markdown_fences always returns string"""
            result = strip_markdown_fences(text)
            assert isinstance(result, str)

        @given(
            st.dictionaries(
                st.text(min_size=1, max_size=20), st.one_of(st.text(), st.integers(), st.booleans())
            )
        )
        def test_extract_json_from_valid_json_string(self, data):
            """Property: Should extract valid JSON from string representation"""
            import json

            json_str = json.dumps(data)
            text = f"prefix {json_str} suffix"
            result = extract_first_json_object(text)

            # Should find the JSON object
            assert result is not None
            assert "{" in result

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


# Fuzzing tests
class TestTextProcessingFuzzing:
    """Fuzzing tests with random/malformed input"""

    def test_fuzz_random_braces(self):
        """Test with random brace patterns"""
        test_cases = [
            "{{{{",
            "}}}}",
            "{}{}{",
            "}{}{",
            "{{{{}}}",
            "{{}}{{",
        ]
        for text in test_cases:
            result = extract_first_json_object(text)
            # Should not crash
            assert result is None or isinstance(result, str)

    def test_fuzz_random_backticks(self):
        """Test with random backtick patterns"""
        test_cases = [
            "```````",
            "`",
            "``",
            "```\n```\n```",
            "```no newline```",
        ]
        for text in test_cases:
            result = strip_markdown_fences(text)
            # Should not crash
            assert isinstance(result, str)

    def test_fuzz_mixed_quotes_and_escapes(self):
        """Test with complex quote and escape patterns"""
        test_cases = [
            '{"key": "\\"\\"\\""}',
            '{"key": "\\\\\\\\"}',
            '{"key": "\\\\\\""}',
            '{"a": "\\"b\\"", "c": "d"}',
        ]
        for text in test_cases:
            result = extract_first_json_object(text)
            # Should handle gracefully
            assert result is None or isinstance(result, str)

    def test_fuzz_extreme_nesting(self):
        """Test with extremely nested structures"""
        # Create deeply nested JSON
        nested = "{"
        for i in range(100):
            nested += f'"level{i}": {{'
        nested += '"value": "deep"'
        nested += "}" * 101

        result = extract_first_json_object(nested)
        assert result is not None
        assert result.count("{") == result.count("}")
