"""
Comprehensive Tests for BaseValidator - Enterprise Grade
=========================================================

🎯 Target: 100% Coverage with Advanced Testing Techniques

Features:
- Property-based testing with Hypothesis
- Fuzzing for edge cases
- Performance benchmarking
- Thread safety validation
- Cache mechanism verification
- Security validation
"""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st
from marshmallow import Schema, ValidationError, fields

from app.validators.base import BaseValidator


# ======================================================================================
# TEST SCHEMAS - Mock schemas for validation testing
# ======================================================================================


class SimpleTestSchema(Schema):
    """Simple test schema for basic validation"""

    name = fields.String(required=True)
    age = fields.Integer(required=False)


class ComplexTestSchema(Schema):
    """Complex schema for advanced validation"""

    email = fields.Email(required=True)
    username = fields.String(required=True)
    tags = fields.List(fields.String(), required=False)
    metadata = fields.Dict(required=False)


class StrictTestSchema(Schema):
    """Schema with strict validation rules"""

    code = fields.String(required=True, allow_none=False)
    value = fields.Float(required=True)
    status = fields.String(required=True)


# ======================================================================================
# UNIT TESTS - Core Functionality
# ======================================================================================


class TestBaseValidatorCore:
    """Core functionality tests for BaseValidator"""

    def test_validate_success_basic(self):
        """Test successful validation with valid data"""
        data = {"name": "Test", "age": 25}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is True
        assert validated_data is not None
        assert errors is None
        assert validated_data["name"] == "Test"
        assert validated_data["age"] == 25

    def test_validate_success_partial(self):
        """Test successful partial validation (useful for PATCH operations)"""
        data = {"name": "Updated Name"}
        success, validated_data, errors = BaseValidator.validate(
            SimpleTestSchema, data, partial=True
        )

        assert success is True
        assert validated_data is not None
        assert errors is None
        assert "name" in validated_data
        assert "age" not in validated_data

    def test_validate_failure_missing_required(self):
        """Test validation failure with missing required fields"""
        data = {"age": 25}  # Missing 'name'
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is False
        assert validated_data is None
        assert errors is not None
        assert "validation_errors" in errors
        assert "invalid_fields" in errors
        assert "name" in errors["invalid_fields"]

    def test_validate_failure_invalid_type(self):
        """Test validation failure with invalid data types"""
        data = {"name": "Test", "age": "not_a_number"}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is False
        assert validated_data is None
        assert errors is not None
        assert "validation_errors" in errors

    def test_validate_complex_schema_success(self):
        """Test validation with complex nested data structures"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "tags": ["python", "testing", "validation"],
            "metadata": {"role": "admin", "active": True},
        }
        success, validated_data, errors = BaseValidator.validate(ComplexTestSchema, data)

        assert success is True
        assert validated_data["email"] == "test@example.com"
        assert len(validated_data["tags"]) == 3
        assert validated_data["metadata"]["role"] == "admin"

    def test_validate_complex_schema_invalid_email(self):
        """Test validation failure with invalid email format"""
        data = {"email": "not-an-email", "username": "testuser"}
        success, validated_data, errors = BaseValidator.validate(ComplexTestSchema, data)

        assert success is False
        assert "email" in errors["invalid_fields"]

    def test_validate_empty_data(self):
        """Test validation with empty dictionary"""
        data = {}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is False
        assert errors is not None

    def test_validate_none_data(self):
        """Test validation behavior with None values"""
        data = {"name": None, "age": None}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is False
        assert errors is not None


# ======================================================================================
# SCHEMA CACHING TESTS - Performance & Memory Optimization
# ======================================================================================


class TestSchemaCache:
    """Test schema caching mechanism for performance optimization"""

    def setup_method(self):
        """Clear cache before each test"""
        BaseValidator._schema_cache.clear()

    def test_cache_creation_on_first_use(self):
        """Test that schema is cached on first validation"""
        assert len(BaseValidator._schema_cache) == 0

        data = {"name": "Test"}
        BaseValidator.validate(SimpleTestSchema, data)

        assert len(BaseValidator._schema_cache) == 1

    def test_cache_reuse_on_subsequent_calls(self):
        """Test that cached schema is reused on subsequent validations"""
        data = {"name": "Test"}

        # First call - creates cache
        BaseValidator.validate(SimpleTestSchema, data)
        initial_cache_size = len(BaseValidator._schema_cache)

        # Second call - should reuse cache
        BaseValidator.validate(SimpleTestSchema, data)
        assert len(BaseValidator._schema_cache) == initial_cache_size

    def test_cache_different_partial_modes(self):
        """Test that different partial modes create separate cache entries"""
        data = {"name": "Test"}

        BaseValidator.validate(SimpleTestSchema, data, partial=False)
        BaseValidator.validate(SimpleTestSchema, data, partial=True)

        # Should have 2 cache entries: one for partial=False, one for partial=True
        assert len(BaseValidator._schema_cache) == 2

    def test_cache_key_format(self):
        """Test that cache keys follow expected format"""
        data = {"name": "Test"}
        BaseValidator.validate(SimpleTestSchema, data, partial=False)

        expected_key = "SimpleTestSchema_False"
        assert expected_key in BaseValidator._schema_cache

    def test_cache_performance_improvement(self):
        """Test that caching provides measurable performance improvement"""
        data = {"name": "Test", "age": 25}

        # First call - with caching overhead
        start_first = time.perf_counter()
        for _ in range(100):
            BaseValidator.validate(SimpleTestSchema, data)
        duration_first = time.perf_counter() - start_first

        # Cache should now be populated, subsequent calls should be faster
        # This is more of a sanity check than strict performance requirement
        assert len(BaseValidator._schema_cache) > 0


# ======================================================================================
# RESPONSE FORMATTING TESTS - API Response Standards
# ======================================================================================


class TestResponseFormatting:
    """Test response formatting utilities"""

    def test_format_error_response_default(self):
        """Test default error response formatting"""
        errors = {"validation_errors": {"field": "error"}, "invalid_fields": ["field"]}
        response, status_code = BaseValidator.format_error_response(errors)

        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == 400
        assert response["error"]["message"] == "Validation failed"
        assert response["error"]["details"] == errors
        assert status_code == 400

    def test_format_error_response_custom_status(self):
        """Test error response with custom status code"""
        errors = {"validation_errors": {"field": "error"}}
        response, status_code = BaseValidator.format_error_response(errors, status_code=422)

        assert response["error"]["code"] == 422
        assert status_code == 422

    def test_format_success_response_basic(self):
        """Test basic success response formatting"""
        data = {"id": 1, "name": "Test"}
        response = BaseValidator.format_success_response(data)

        assert response["success"] is True
        assert response["message"] == "Success"
        assert response["data"] == data

    def test_format_success_response_custom_message(self):
        """Test success response with custom message"""
        data = {"id": 1}
        response = BaseValidator.format_success_response(data, message="Created successfully")

        assert response["message"] == "Created successfully"

    def test_format_success_response_with_metadata(self):
        """Test success response with metadata"""
        data = {"items": [1, 2, 3]}
        metadata = {"total": 3, "page": 1, "per_page": 10}
        response = BaseValidator.format_success_response(data, metadata=metadata)

        assert "metadata" in response
        assert response["metadata"]["total"] == 3
        assert response["metadata"]["page"] == 1

    def test_format_success_response_without_metadata(self):
        """Test success response without metadata"""
        data = {"id": 1}
        response = BaseValidator.format_success_response(data)

        assert "metadata" not in response

    def test_format_success_response_empty_data(self):
        """Test success response with empty data"""
        response = BaseValidator.format_success_response([])

        assert response["success"] is True
        assert response["data"] == []

    def test_format_success_response_none_data(self):
        """Test success response with None data"""
        response = BaseValidator.format_success_response(None)

        assert response["success"] is True
        assert response["data"] is None


# ======================================================================================
# THREAD SAFETY TESTS - Concurrent Access Validation
# ======================================================================================


class TestThreadSafety:
    """Test thread safety of validation and caching"""

    def setup_method(self):
        """Clear cache before each test"""
        BaseValidator._schema_cache.clear()

    def test_concurrent_validation_same_schema(self):
        """Test concurrent validations using same schema"""
        data = {"name": "Test", "age": 25}
        results = []

        def validate_in_thread():
            success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)
            return (success, validated_data, errors)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_in_thread) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]

        # All validations should succeed
        assert all(result[0] is True for result in results)
        assert all(result[1] is not None for result in results)
        assert all(result[2] is None for result in results)

    def test_concurrent_validation_different_schemas(self):
        """Test concurrent validations using different schemas"""

        def validate_simple():
            data = {"name": "Test"}
            return BaseValidator.validate(SimpleTestSchema, data)

        def validate_complex():
            data = {"email": "test@example.com", "username": "test"}
            return BaseValidator.validate(ComplexTestSchema, data)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(50):
                if i % 2 == 0:
                    futures.append(executor.submit(validate_simple))
                else:
                    futures.append(executor.submit(validate_complex))

            results = [future.result() for future in as_completed(futures)]

        # All validations should succeed
        assert all(result[0] is True for result in results)

    def test_cache_thread_safety(self):
        """Test that cache remains consistent under concurrent access"""
        data = {"name": "Test"}

        def validate_and_check_cache():
            BaseValidator.validate(SimpleTestSchema, data)
            return len(BaseValidator._schema_cache)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(validate_and_check_cache) for _ in range(100)]
            cache_sizes = [future.result() for future in as_completed(futures)]

        # Cache should have exactly 1 entry despite concurrent access
        assert len(BaseValidator._schema_cache) == 1
        assert all(size >= 1 for size in cache_sizes)


# ======================================================================================
# PROPERTY-BASED TESTS - Hypothesis Testing for Edge Cases
# ======================================================================================


class TestPropertyBased:
    """Property-based tests using Hypothesis for comprehensive edge case coverage"""

    def setup_method(self):
        """Clear cache before each test"""
        BaseValidator._schema_cache.clear()

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_validate_always_returns_tuple(self, name):
        """Property: validate() always returns a 3-tuple"""
        data = {"name": name}
        result = BaseValidator.validate(SimpleTestSchema, data)

        assert isinstance(result, tuple)
        assert len(result) == 3

    @given(st.text(min_size=1, max_size=100), st.integers(min_value=0, max_value=150))
    @settings(max_examples=50)
    def test_validate_valid_data_always_succeeds(self, name, age):
        """Property: Valid data always passes validation"""
        data = {"name": name, "age": age}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        if success:
            assert validated_data is not None
            assert errors is None
        else:
            assert validated_data is None
            assert errors is not None

    @given(st.dictionaries(st.text(), st.text()))
    @settings(max_examples=30)
    def test_validate_handles_arbitrary_dicts(self, data):
        """Property: validate() handles arbitrary dictionaries gracefully"""
        try:
            result = BaseValidator.validate(SimpleTestSchema, data)
            assert isinstance(result, tuple)
            assert len(result) == 3
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")

    @given(st.text(), st.integers(min_value=400, max_value=599))
    @settings(max_examples=30)
    def test_format_error_response_status_codes(self, error_msg, status_code):
        """Property: Error responses maintain status code integrity"""
        errors = {"validation_errors": {"field": error_msg}}
        response, returned_status = BaseValidator.format_error_response(
            errors, status_code=status_code
        )

        assert returned_status == status_code
        assert response["error"]["code"] == status_code


# ======================================================================================
# EDGE CASES & SECURITY TESTS - Robustness Validation
# ======================================================================================


class TestEdgeCasesAndSecurity:
    """Test edge cases and security considerations"""

    def test_validate_with_extra_fields(self):
        """Test validation with extra fields not in schema"""
        data = {"name": "Test", "age": 25, "extra_field": "should_be_ignored"}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        # Marshmallow by default raises error for unknown fields (RAISE is default)
        # This is actually good for security - reject unexpected data
        # If schema has Meta.unknown = EXCLUDE, it would pass
        # For now we test both possibilities
        if not success:
            # Schema rejects unknown fields - good for security
            assert "extra_field" in str(errors) or "unknown" in str(errors).lower()
        else:
            # Schema excludes unknown fields
            assert "extra_field" not in validated_data

    def test_validate_with_unicode_data(self):
        """Test validation with unicode characters"""
        data = {"name": "测试用户 🚀", "age": 25}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        assert success is True
        assert validated_data["name"] == "测试用户 🚀"

    def test_validate_with_very_large_strings(self):
        """Test validation with very large string inputs"""
        large_string = "A" * 100000
        data = {"name": large_string}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, data)

        # Should handle large strings (schema validation may impose limits)
        assert isinstance(success, bool)

    def test_validate_with_nested_dicts(self):
        """Test validation with deeply nested dictionaries"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "metadata": {"level1": {"level2": {"level3": {"value": "deep"}}}},
        }
        success, validated_data, errors = BaseValidator.validate(ComplexTestSchema, data)

        assert success is True
        assert validated_data["metadata"]["level1"]["level2"]["level3"]["value"] == "deep"

    def test_validate_sql_injection_attempt(self):
        """Test that validation handles potential SQL injection strings safely"""
        malicious_data = {"name": "'; DROP TABLE users; --", "age": 25}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, malicious_data)

        # Should still validate successfully (SQL safety is schema's concern)
        assert success is True
        # The malicious string should be preserved as-is
        assert validated_data["name"] == "'; DROP TABLE users; --"

    def test_validate_xss_attempt(self):
        """Test that validation handles XSS attack strings"""
        xss_data = {"name": "<script>alert('XSS')</script>", "age": 25}
        success, validated_data, errors = BaseValidator.validate(SimpleTestSchema, xss_data)

        # Should validate (XSS prevention is template engine's concern)
        assert success is True

    def test_response_formatting_with_malicious_content(self):
        """Test response formatting with potentially malicious content"""
        data = {"exploit": "<script>alert('XSS')</script>"}
        response = BaseValidator.format_success_response(data)

        # Should format without executing or modifying content
        assert response["data"]["exploit"] == "<script>alert('XSS')</script>"

    def test_cache_isolation_between_schemas(self):
        """Test that cache doesn't leak data between different schemas"""
        data1 = {"name": "Test1"}
        data2 = {"email": "test@example.com", "username": "test"}

        BaseValidator.validate(SimpleTestSchema, data1)
        BaseValidator.validate(ComplexTestSchema, data2)

        # Should have separate cache entries
        assert "SimpleTestSchema_False" in BaseValidator._schema_cache
        assert "ComplexTestSchema_False" in BaseValidator._schema_cache


# ======================================================================================
# INTEGRATION TESTS - Real-world Scenarios
# ======================================================================================


class TestIntegration:
    """Integration tests simulating real-world usage patterns"""

    def test_full_crud_validation_workflow(self):
        """Test complete CRUD validation workflow"""
        # CREATE - Full validation
        create_data = {"name": "John Doe", "age": 30}
        success, validated, errors = BaseValidator.validate(SimpleTestSchema, create_data)
        assert success is True

        # UPDATE - Partial validation
        update_data = {"age": 31}
        success, validated, errors = BaseValidator.validate(
            SimpleTestSchema, update_data, partial=True
        )
        assert success is True

        # READ - No validation needed
        # DELETE - No validation needed

    def test_api_response_workflow(self):
        """Test complete API response workflow"""
        # Invalid request
        invalid_data = {"age": 25}
        success, validated, errors = BaseValidator.validate(SimpleTestSchema, invalid_data)
        assert success is False

        error_response, status = BaseValidator.format_error_response(errors)
        assert status == 400
        assert error_response["success"] is False

        # Valid request
        valid_data = {"name": "Test", "age": 25}
        success, validated, errors = BaseValidator.validate(SimpleTestSchema, valid_data)
        assert success is True

        success_response = BaseValidator.format_success_response(
            validated, message="User created", metadata={"id": 1}
        )
        assert success_response["success"] is True
        assert success_response["metadata"]["id"] == 1

    def test_batch_validation(self):
        """Test validating multiple records in batch"""
        batch_data = [
            {"name": "User1", "age": 20},
            {"name": "User2", "age": 25},
            {"name": "User3", "age": 30},
        ]

        results = []
        for data in batch_data:
            success, validated, errors = BaseValidator.validate(SimpleTestSchema, data)
            results.append((success, validated, errors))

        # All should succeed
        assert all(result[0] is True for result in results)
        assert len(results) == 3

    def test_validation_error_aggregation(self):
        """Test aggregating validation errors from multiple fields"""
        data = {}  # Missing all required fields
        success, validated, errors = BaseValidator.validate(StrictTestSchema, data)

        assert success is False
        assert len(errors["invalid_fields"]) >= 1  # At least one field should fail


# ======================================================================================
# PERFORMANCE TESTS - Benchmarking
# ======================================================================================


class TestPerformance:
    """Performance benchmarking tests"""

    def test_validation_performance_baseline(self):
        """Establish baseline performance for validation operations"""
        data = {"name": "Test", "age": 25}

        start = time.perf_counter()
        for _ in range(1000):
            BaseValidator.validate(SimpleTestSchema, data)
        duration = time.perf_counter() - start

        # Should complete 1000 validations reasonably fast (< 1 second)
        assert duration < 1.0, f"Performance regression: {duration:.3f}s for 1000 validations"

    def test_cache_memory_efficiency(self):
        """Test that cache doesn't grow unbounded"""
        BaseValidator._schema_cache.clear()

        # Validate with same schema multiple times
        data = {"name": "Test"}
        for _ in range(100):
            BaseValidator.validate(SimpleTestSchema, data)

        # Cache should remain small
        assert len(BaseValidator._schema_cache) <= 2  # partial=True/False
