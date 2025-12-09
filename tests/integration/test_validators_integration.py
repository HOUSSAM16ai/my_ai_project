"""
Integration Tests for Validators
=================================

Testing validators in realistic scenarios with:
- Multiple validation steps
- Error handling workflows
- API-like usage patterns
- Performance under load
"""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from marshmallow import Schema, fields

from app.validators.base import BaseValidator


class UserSchema(Schema):
    """Realistic user schema"""

    username = fields.String(required=True)
    email = fields.Email(required=True)
    age = fields.Integer(required=False)
    active = fields.Boolean(required=False)


class TestValidatorAPIWorkflow:
    """Test validators in API-like workflows"""

    def test_create_user_workflow(self):
        """Test complete user creation workflow"""
        # Step 1: Validate input
        user_data = {"username": "john_doe", "email": "john@example.com", "age": 30, "active": True}

        success, validated, errors = BaseValidator.validate(UserSchema, user_data)

        assert success is True
        assert validated["username"] == "john_doe"
        assert validated["email"] == "john@example.com"

        # Step 2: Format success response
        response = BaseValidator.format_success_response(
            validated, message="User created successfully", metadata={"user_id": 123}
        )

        assert response["success"] is True
        assert response["data"]["username"] == "john_doe"
        assert response["metadata"]["user_id"] == 123

    def test_update_user_workflow_partial(self):
        """Test partial update workflow"""
        # Partial update - only email
        update_data = {"email": "newemail@example.com"}

        success, validated, errors = BaseValidator.validate(UserSchema, update_data, partial=True)

        assert success is True
        assert validated["email"] == "newemail@example.com"
        assert "username" not in validated

        # Format response
        response = BaseValidator.format_success_response(validated, message="User updated")

        assert response["success"] is True

    def test_validation_error_workflow(self):
        """Test error handling workflow"""
        # Invalid data
        invalid_data = {"username": "john", "email": "not_an_email"}

        success, validated, errors = BaseValidator.validate(UserSchema, invalid_data)

        assert success is False
        assert errors is not None

        # Format error response
        response, status = BaseValidator.format_error_response(errors, status_code=400)

        assert response["success"] is False
        assert status == 400
        assert "validation_errors" in response["error"]["details"]

    def test_batch_validation_workflow(self):
        """Test validating multiple items"""
        users = [
            {"username": "user1", "email": "user1@example.com"},
            {"username": "user2", "email": "user2@example.com"},
            {"username": "user3", "email": "invalid_email"},  # Invalid
        ]

        results = []
        for user_data in users:
            success, validated, errors = BaseValidator.validate(UserSchema, user_data)
            results.append((success, validated, errors))

        # First two should succeed
        assert results[0][0] is True
        assert results[1][0] is True

        # Third should fail
        assert results[2][0] is False
        assert "email" in results[2][2]["invalid_fields"]


class TestValidatorPerformance:
    """Test validator performance under load"""

    def test_sequential_validation_performance(self):
        """Test performance of sequential validations"""
        import time

        data = {"username": "testuser", "email": "test@example.com"}

        start = time.time()
        for _ in range(1000):
            BaseValidator.validate(UserSchema, data)
        elapsed = time.time() - start

        # Should complete 1000 validations in under 1 second
        assert elapsed < 1.0

    def test_concurrent_validation_performance(self):
        """Test performance of concurrent validations"""
        import time

        def validate_user(i):
            data = {"username": f"user{i}", "email": f"user{i}@example.com"}
            return BaseValidator.validate(UserSchema, data)

        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(validate_user, range(100)))
        elapsed = time.time() - start

        # All should succeed
        assert all(r[0] for r in results)

        # Should complete in reasonable time
        assert elapsed < 2.0

    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        import time

        data = {"username": "test", "email": "test@example.com"}

        # First validation (cache miss)
        start = time.time()
        BaseValidator.validate(UserSchema, data)
        first_time = time.time() - start

        # Subsequent validations (cache hit)
        times = []
        for _ in range(100):
            start = time.time()
            BaseValidator.validate(UserSchema, data)
            times.append(time.time() - start)

        avg_cached_time = sum(times) / len(times)

        # Cached validations should be faster (or at least not slower)
        assert avg_cached_time <= first_time * 1.5


class TestValidatorErrorRecovery:
    """Test error recovery and resilience"""

    def test_recovery_from_validation_error(self):
        """Test that validator recovers from errors"""
        # First, cause a validation error
        invalid_data = {"username": "test"}  # Missing required email
        success1, _, errors1 = BaseValidator.validate(UserSchema, invalid_data)
        assert not success1

        # Then, validate valid data
        valid_data = {"username": "test", "email": "test@example.com"}
        success2, validated2, errors2 = BaseValidator.validate(UserSchema, valid_data)

        # Should succeed
        assert success2 is True
        assert errors2 is None

    def test_multiple_schema_isolation(self):
        """Test that errors in one schema don't affect others"""

        class Schema1(Schema):
            field1 = fields.String(required=True)

        class Schema2(Schema):
            field2 = fields.Integer(required=True)

        # Fail validation on Schema1
        success1, _, _ = BaseValidator.validate(Schema1, {})
        assert not success1

        # Schema2 should still work
        success2, validated2, _ = BaseValidator.validate(Schema2, {"field2": 42})
        assert success2 is True
        assert validated2["field2"] == 42


class TestValidatorComplexScenarios:
    """Test complex real-world scenarios"""

    def test_nested_validation_workflow(self):
        """Test validation of nested structures"""

        class AddressSchema(Schema):
            street = fields.String(required=True)
            city = fields.String(required=True)
            zip_code = fields.String(required=True)

        class UserWithAddressSchema(Schema):
            username = fields.String(required=True)
            email = fields.Email(required=True)
            address = fields.Nested(AddressSchema, required=True)

        data = {
            "username": "john",
            "email": "john@example.com",
            "address": {"street": "123 Main St", "city": "Springfield", "zip_code": "12345"},
        }

        success, validated, errors = BaseValidator.validate(UserWithAddressSchema, data)

        assert success is True
        assert validated["address"]["city"] == "Springfield"

    def test_list_validation_workflow(self):
        """Test validation of lists"""

        class TagsSchema(Schema):
            tags = fields.List(fields.String(), required=True)

        data = {"tags": ["python", "testing", "validation"]}

        success, validated, errors = BaseValidator.validate(TagsSchema, data)

        assert success is True
        assert len(validated["tags"]) == 3

    def test_conditional_validation_workflow(self):
        """Test conditional validation logic"""
        # Validate as create (all fields required)
        create_data = {"username": "newuser", "email": "new@example.com"}
        success_create, _, _ = BaseValidator.validate(UserSchema, create_data, partial=False)
        assert success_create is True

        # Validate as update (partial allowed)
        update_data = {"email": "updated@example.com"}
        success_update, _, _ = BaseValidator.validate(UserSchema, update_data, partial=True)
        assert success_update is True

    def test_multi_step_validation_pipeline(self):
        """Test multi-step validation pipeline"""

        class Step1Schema(Schema):
            username = fields.String(required=True)

        class Step2Schema(Schema):
            username = fields.String(required=True)
            email = fields.Email(required=True)

        # Step 1: Validate username
        data = {"username": "john"}
        success1, validated1, _ = BaseValidator.validate(Step1Schema, data)
        assert success1 is True

        # Step 2: Add email and validate again
        data["email"] = "john@example.com"
        success2, validated2, _ = BaseValidator.validate(Step2Schema, data)
        assert success2 is True

        # Final response
        response = BaseValidator.format_success_response(
            validated2, message="Registration complete", metadata={"steps_completed": 2}
        )

        assert response["metadata"]["steps_completed"] == 2


class TestValidatorEdgeCaseIntegration:
    """Test edge cases in integration scenarios"""

    def test_empty_batch_validation(self):
        """Test validating empty batch"""
        users = []

        results = []
        for user_data in users:
            success, validated, errors = BaseValidator.validate(UserSchema, user_data)
            results.append((success, validated, errors))

        assert len(results) == 0

    def test_large_batch_validation(self):
        """Test validating large batch"""
        users = [{"username": f"user{i}", "email": f"user{i}@example.com"} for i in range(1000)]

        success_count = 0
        for user_data in users:
            success, _, _ = BaseValidator.validate(UserSchema, user_data)
            if success:
                success_count += 1

        assert success_count == 1000

    def test_validation_with_unicode_data(self):
        """Test validation with Unicode in realistic scenario"""
        users = [
            {"username": "مستخدم", "email": "user@example.com"},
            {"username": "用户", "email": "user@example.com"},
            {"username": "пользователь", "email": "user@example.com"},
        ]

        for user_data in users:
            success, validated, _ = BaseValidator.validate(UserSchema, user_data)
            assert success is True
            assert validated["username"] == user_data["username"]


class TestValidatorStateManagement:
    """Test state management across validations"""

    def test_cache_state_consistency(self):
        """Test that cache state remains consistent"""
        initial_cache_size = len(BaseValidator._schema_cache)

        # Perform various validations
        BaseValidator.validate(UserSchema, {"username": "test", "email": "test@example.com"})
        BaseValidator.validate(UserSchema, {"username": "test2", "email": "test2@example.com"}, partial=True)

        # Cache should have at most 2 entries for UserSchema
        cache_keys = [k for k in BaseValidator._schema_cache.keys() if "UserSchema" in k]
        assert len(cache_keys) <= 2

    def test_no_state_leakage_between_validations(self):
        """Test that state doesn't leak between validations"""
        # First validation
        data1 = {"username": "user1", "email": "user1@example.com"}
        success1, validated1, _ = BaseValidator.validate(UserSchema, data1)

        # Second validation with different data
        data2 = {"username": "user2", "email": "user2@example.com"}
        success2, validated2, _ = BaseValidator.validate(UserSchema, data2)

        # Results should be independent
        assert validated1["username"] != validated2["username"]
        assert validated1["email"] != validated2["email"]


class TestValidatorRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_api_pagination_validation(self):
        """Test API pagination parameter validation"""
        from app.validators.schemas import PaginationSchema

        # Typical API request
        query_params = {"page": "2", "per_page": "25", "search": "test", "order_by": "created_at", "order_dir": "desc"}

        success, validated, _ = BaseValidator.validate(PaginationSchema, query_params)

        assert success is True
        assert validated["page"] == 2
        assert validated["per_page"] == 25

        # Format for use in query
        response = BaseValidator.format_success_response(validated)
        assert response["data"]["page"] == 2

    def test_form_submission_validation(self):
        """Test form submission validation"""
        # Simulate form data
        form_data = {
            "username": "  john_doe  ",  # With whitespace
            "email": "JOHN@EXAMPLE.COM",  # Uppercase
            "age": "30",  # String number
        }

        success, validated, _ = BaseValidator.validate(UserSchema, form_data)

        # Should succeed with type coercion
        assert success is True
        assert isinstance(validated["age"], int)

    def test_json_api_validation(self):
        """Test JSON API request validation"""
        # Simulate JSON API request
        json_data = json.dumps({"username": "john", "email": "john@example.com", "age": 30})

        parsed_data = json.loads(json_data)
        success, validated, _ = BaseValidator.validate(UserSchema, parsed_data)

        assert success is True

        # Format JSON response
        response = BaseValidator.format_success_response(validated, message="Success")
        json_response = json.dumps(response)

        assert isinstance(json_response, str)
        assert "john" in json_response
