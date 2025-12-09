"""
Comprehensive Unit Tests for BaseValidator
===========================================

Coverage Target: 100%
Testing Strategy:
- All methods and branches
- Edge cases and boundary conditions
- Error handling paths
- Cache behavior
- Type validation
"""

import pytest
from marshmallow import Schema, ValidationError, fields

from app.validators.base import BaseValidator


# Test Schemas
class SimpleSchema(Schema):
    """Simple test schema"""

    name = fields.String(required=True)
    age = fields.Integer(required=False)


class ComplexSchema(Schema):
    """Complex test schema with nested validation"""

    email = fields.Email(required=True)
    username = fields.String(required=True)
    age = fields.Integer(required=False)
    tags = fields.List(fields.String(), required=False)


class TestBaseValidatorValidate:
    """Test validate() method - all branches and edge cases"""

    def test_validate_success_with_valid_data(self):
        """Test successful validation with all required fields"""
        data = {"name": "John Doe", "age": 30}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True
        assert validated == {"name": "John Doe", "age": 30}
        assert errors is None

    def test_validate_success_with_minimal_data(self):
        """Test validation with only required fields"""
        data = {"name": "Jane"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True
        assert validated["name"] == "Jane"
        assert "age" not in validated or validated["age"] is None
        assert errors is None

    def test_validate_failure_missing_required_field(self):
        """Test validation failure when required field is missing"""
        data = {"age": 25}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is False
        assert validated is None
        assert errors is not None
        assert "validation_errors" in errors
        assert "invalid_fields" in errors
        assert "name" in errors["invalid_fields"]

    def test_validate_failure_invalid_type(self):
        """Test validation failure with wrong data type"""
        data = {"name": "John", "age": "not_a_number"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is False
        assert validated is None
        assert errors is not None
        assert "age" in errors["invalid_fields"]

    def test_validate_with_partial_true(self):
        """Test partial validation allows missing required fields"""
        data = {"age": 30}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data, partial=True)

        assert success is True
        assert validated == {"age": 30}
        assert errors is None

    def test_validate_with_partial_false(self):
        """Test non-partial validation requires all fields"""
        data = {"age": 30}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data, partial=False)

        assert success is False
        assert "name" in errors["invalid_fields"]

    def test_validate_empty_data(self):
        """Test validation with empty dictionary"""
        data = {}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is False
        assert "name" in errors["invalid_fields"]

    def test_validate_complex_schema_success(self):
        """Test validation with complex nested schema"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "age": 25,
            "tags": ["python", "testing"],
        }
        success, validated, errors = BaseValidator.validate(ComplexSchema, data)

        assert success is True
        assert validated["email"] == "test@example.com"
        assert validated["tags"] == ["python", "testing"]
        assert errors is None

    def test_validate_complex_schema_invalid_email(self):
        """Test validation failure with invalid email format"""
        data = {"email": "not_an_email", "username": "testuser"}
        success, validated, errors = BaseValidator.validate(ComplexSchema, data)

        assert success is False
        assert "email" in errors["invalid_fields"]

    def test_validate_extra_fields_ignored(self):
        """Test that extra fields not in schema are handled"""
        data = {"name": "John", "extra_field": "ignored"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        # Marshmallow by default ignores unknown fields
        assert success is True
        assert "extra_field" not in validated

    def test_validate_none_values(self):
        """Test validation with None values for optional fields"""
        data = {"name": "John", "age": None}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True
        assert validated["name"] == "John"

    def test_validate_schema_caching(self):
        """Test that schema instances are cached for performance"""
        data1 = {"name": "First"}
        data2 = {"name": "Second"}

        # First call creates cache entry
        BaseValidator.validate(SimpleSchema, data1)
        cache_size_before = len(BaseValidator._schema_cache)

        # Second call should reuse cached schema
        BaseValidator.validate(SimpleSchema, data2)
        cache_size_after = len(BaseValidator._schema_cache)

        assert cache_size_before == cache_size_after

    def test_validate_different_partial_creates_separate_cache(self):
        """Test that partial=True and partial=False create separate cache entries"""
        data = {"name": "Test"}

        BaseValidator.validate(SimpleSchema, data, partial=False)
        cache_size_1 = len(BaseValidator._schema_cache)

        BaseValidator.validate(SimpleSchema, data, partial=True)
        cache_size_2 = len(BaseValidator._schema_cache)

        # Should have 2 entries: one for partial=False, one for partial=True
        assert cache_size_2 > cache_size_1


class TestBaseValidatorFormatErrorResponse:
    """Test format_error_response() method"""

    def test_format_error_response_default_status(self):
        """Test error response formatting with default status code"""
        errors = {"validation_errors": {"field": "error"}, "invalid_fields": ["field"]}
        response, status = BaseValidator.format_error_response(errors)

        assert status == 400
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == 400
        assert response["error"]["message"] == "Validation failed"
        assert response["error"]["details"] == errors

    def test_format_error_response_custom_status(self):
        """Test error response formatting with custom status code"""
        errors = {"validation_errors": {"field": "error"}}
        response, status = BaseValidator.format_error_response(errors, status_code=422)

        assert status == 422
        assert response["error"]["code"] == 422

    def test_format_error_response_empty_errors(self):
        """Test error response with empty errors dict"""
        errors = {}
        response, status = BaseValidator.format_error_response(errors)

        assert response["success"] is False
        assert response["error"]["details"] == {}

    def test_format_error_response_complex_errors(self):
        """Test error response with nested error structure"""
        errors = {
            "validation_errors": {
                "email": ["Invalid email format", "Email already exists"],
                "password": ["Too short"],
            },
            "invalid_fields": ["email", "password"],
        }
        response, status = BaseValidator.format_error_response(errors)

        assert response["error"]["details"]["validation_errors"]["email"] == [
            "Invalid email format",
            "Email already exists",
        ]


class TestBaseValidatorFormatSuccessResponse:
    """Test format_success_response() method"""

    def test_format_success_response_basic(self):
        """Test success response with basic data"""
        data = {"id": 1, "name": "Test"}
        response = BaseValidator.format_success_response(data)

        assert response["success"] is True
        assert response["message"] == "Success"
        assert response["data"] == data
        assert "metadata" not in response

    def test_format_success_response_custom_message(self):
        """Test success response with custom message"""
        data = {"id": 1}
        response = BaseValidator.format_success_response(data, message="Created successfully")

        assert response["message"] == "Created successfully"

    def test_format_success_response_with_metadata(self):
        """Test success response with metadata"""
        data = {"items": [1, 2, 3]}
        metadata = {"total": 3, "page": 1}
        response = BaseValidator.format_success_response(data, metadata=metadata)

        assert response["metadata"] == metadata
        assert response["metadata"]["total"] == 3

    def test_format_success_response_none_data(self):
        """Test success response with None as data"""
        response = BaseValidator.format_success_response(None)

        assert response["success"] is True
        assert response["data"] is None

    def test_format_success_response_empty_list(self):
        """Test success response with empty list"""
        response = BaseValidator.format_success_response([])

        assert response["data"] == []

    def test_format_success_response_empty_dict(self):
        """Test success response with empty dict"""
        response = BaseValidator.format_success_response({})

        assert response["data"] == {}

    def test_format_success_response_complex_data(self):
        """Test success response with nested complex data"""
        data = {
            "user": {"id": 1, "name": "John", "roles": ["admin", "user"]},
            "permissions": ["read", "write"],
        }
        response = BaseValidator.format_success_response(data)

        assert response["data"]["user"]["roles"] == ["admin", "user"]


class TestBaseValidatorEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_validate_with_unicode_data(self):
        """Test validation with Unicode characters"""
        data = {"name": "مستخدم عربي"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True
        assert validated["name"] == "مستخدم عربي"

    def test_validate_with_very_long_string(self):
        """Test validation with very long string"""
        data = {"name": "A" * 10000}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True
        assert len(validated["name"]) == 10000

    def test_validate_with_special_characters(self):
        """Test validation with special characters"""
        data = {"name": "Test!@#$%^&*()_+-=[]{}|;:',.<>?/~`"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        assert success is True

    def test_validate_boundary_integer_values(self):
        """Test validation with boundary integer values"""
        test_cases = [
            {"name": "Test", "age": 0},
            {"name": "Test", "age": -1},
            {"name": "Test", "age": 2**31 - 1},
        ]

        for data in test_cases:
            success, validated, errors = BaseValidator.validate(SimpleSchema, data)
            assert success is True

    def test_cache_key_generation_consistency(self):
        """Test that cache keys are generated consistently"""
        # Validate multiple times with same schema and partial setting
        for _ in range(5):
            BaseValidator.validate(SimpleSchema, {"name": "Test"}, partial=False)

        # Cache should not grow beyond necessary entries
        cache_keys = [k for k in BaseValidator._schema_cache.keys() if "SimpleSchema" in k]
        assert len(cache_keys) <= 2  # One for partial=True, one for partial=False


class TestBaseValidatorIntegration:
    """Integration tests combining multiple methods"""

    def test_full_validation_flow_success(self):
        """Test complete validation flow from input to formatted response"""
        data = {"name": "John Doe", "age": 30}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        if success:
            response = BaseValidator.format_success_response(
                validated, message="User validated successfully"
            )
            assert response["success"] is True
            assert response["data"]["name"] == "John Doe"

    def test_full_validation_flow_failure(self):
        """Test complete validation flow with error formatting"""
        data = {"age": "invalid"}
        success, validated, errors = BaseValidator.validate(SimpleSchema, data)

        if not success:
            response, status = BaseValidator.format_error_response(errors)
            assert response["success"] is False
            assert status == 400
            assert "validation_errors" in response["error"]["details"]

    def test_multiple_schemas_cached_independently(self):
        """Test that different schemas are cached independently"""
        simple_data = {"name": "Test"}
        complex_data = {"email": "test@example.com", "username": "test"}

        BaseValidator.validate(SimpleSchema, simple_data)
        BaseValidator.validate(ComplexSchema, complex_data)

        # Both schemas should be in cache
        assert any("SimpleSchema" in k for k in BaseValidator._schema_cache.keys())
        assert any("ComplexSchema" in k for k in BaseValidator._schema_cache.keys())


# Property-based tests using Hypothesis
try:
    from hypothesis import given
    from hypothesis import strategies as st

    class TestBaseValidatorPropertyBased:
        """Property-based tests for BaseValidator"""

        @given(st.text(min_size=1, max_size=100))
        def test_validate_any_string_name(self, name):
            """Property: Any non-empty string should be valid for name field"""
            data = {"name": name}
            success, validated, errors = BaseValidator.validate(SimpleSchema, data)

            assert success is True
            assert validated["name"] == name

        @given(st.integers())
        def test_validate_any_integer_age(self, age):
            """Property: Any integer should be valid for age field"""
            data = {"name": "Test", "age": age}
            success, validated, errors = BaseValidator.validate(SimpleSchema, data)

            assert success is True
            assert validated["age"] == age

        @given(st.dictionaries(st.text(), st.text()))
        def test_format_success_response_any_dict(self, data):
            """Property: format_success_response should work with any dict"""
            response = BaseValidator.format_success_response(data)

            assert response["success"] is True
            assert response["data"] == data

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass
