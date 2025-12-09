"""
Property-Based Tests for Validators
====================================

Using Hypothesis for property-based testing to discover edge cases
and verify invariants across large input spaces.

Strategy:
- Define properties that should always hold
- Generate thousands of test cases automatically
- Discover edge cases humans might miss
"""

import json

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from marshmallow import Schema, fields

from app.validators.base import BaseValidator


# Test schemas for property-based testing
class FlexibleSchema(Schema):
    """Schema that accepts various types"""

    text = fields.String(required=False)
    number = fields.Integer(required=False)
    flag = fields.Boolean(required=False)


class StrictSchema(Schema):
    """Schema with strict requirements"""

    required_field = fields.String(required=True)
    email = fields.Email(required=True)


@settings(max_examples=500, deadline=None)
class TestBaseValidatorProperties:
    """Property-based tests for BaseValidator"""

    @given(st.text(min_size=1, max_size=1000))
    def test_property_validate_always_returns_tuple(self, text):
        """Property: validate() always returns a 3-tuple"""
        data = {"text": text}
        result = BaseValidator.validate(FlexibleSchema, data)

        assert isinstance(result, tuple)
        assert len(result) == 3
        success, validated, errors = result
        assert isinstance(success, bool)

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=10))
    def test_property_validate_success_implies_no_errors(self, data):
        """Property: If validation succeeds, errors must be None"""
        success, validated, errors = BaseValidator.validate(FlexibleSchema, data)

        if success:
            assert errors is None
            assert validated is not None

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=10))
    def test_property_validate_failure_implies_errors(self, data):
        """Property: If validation fails, errors must not be None"""
        success, validated, errors = BaseValidator.validate(StrictSchema, data)

        if not success:
            assert errors is not None
            assert validated is None
            assert "validation_errors" in errors

    @given(st.integers())
    def test_property_format_error_response_structure(self, status_code):
        """Property: Error response always has correct structure"""
        assume(100 <= status_code <= 599)  # Valid HTTP status codes

        errors = {"validation_errors": {"field": "error"}}
        response, status = BaseValidator.format_error_response(errors, status_code)

        assert isinstance(response, dict)
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == status_code
        assert status == status_code

    @given(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        )
    )
    def test_property_format_success_response_accepts_any_data(self, data):
        """Property: Success response accepts any JSON-serializable data"""
        response = BaseValidator.format_success_response(data)

        assert response["success"] is True
        assert "data" in response
        assert response["data"] == data

    @given(st.text(min_size=1, max_size=100))
    def test_property_success_message_preserved(self, message):
        """Property: Custom message is preserved in success response"""
        response = BaseValidator.format_success_response({}, message=message)

        assert response["message"] == message

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.integers(), max_size=5))
    def test_property_metadata_preserved(self, metadata):
        """Property: Metadata is preserved in success response"""
        response = BaseValidator.format_success_response({}, metadata=metadata)

        assert "metadata" in response
        assert response["metadata"] == metadata

    @given(st.text(min_size=1, max_size=100))
    def test_property_validate_idempotent(self, text):
        """Property: Validating same data twice gives same result"""
        data = {"text": text}

        result1 = BaseValidator.validate(FlexibleSchema, data)
        result2 = BaseValidator.validate(FlexibleSchema, data)

        assert result1[0] == result2[0]  # Same success status
        if result1[0]:
            assert result1[1] == result2[1]  # Same validated data

    @given(st.integers(min_value=1, max_value=100))
    def test_property_cache_grows_bounded(self, iterations):
        """Property: Schema cache doesn't grow unboundedly"""
        initial_size = len(BaseValidator._schema_cache)

        for _ in range(iterations):
            BaseValidator.validate(FlexibleSchema, {"text": "test"})

        final_size = len(BaseValidator._schema_cache)

        # Cache should not grow linearly with validations
        assert final_size - initial_size <= 2  # At most 2 entries per schema

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20))
    def test_property_invalid_fields_list_valid(self, field_names):
        """Property: invalid_fields is always a list"""
        # Create data missing required field
        data = {field: "value" for field in field_names if field != "required_field"}

        success, validated, errors = BaseValidator.validate(StrictSchema, data)

        if not success:
            assert isinstance(errors["invalid_fields"], list)
            assert all(isinstance(f, str) for f in errors["invalid_fields"])


@settings(max_examples=300, deadline=None)
class TestValidationInvariants:
    """Test invariants that should always hold"""

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100)))
    def test_invariant_success_xor_failure(self, data):
        """Invariant: Validation either succeeds OR fails, never both"""
        success, validated, errors = BaseValidator.validate(FlexibleSchema, data)

        # Exactly one of these should be true
        assert (success and errors is None) or (not success and errors is not None)
        assert not (success and errors is not None)
        assert not (not success and errors is None)

    @given(st.text(min_size=1, max_size=100))
    def test_invariant_required_field_enforcement(self, value):
        """Invariant: Required fields are always enforced"""
        # Data without required field
        data_without = {"other": value}
        success1, _, errors1 = BaseValidator.validate(StrictSchema, data_without)
        assert not success1
        assert "required_field" in errors1["invalid_fields"]

        # Data with required field
        data_with = {"required_field": value, "email": "test@example.com"}
        success2, _, _ = BaseValidator.validate(StrictSchema, data_with)
        assert success2

    @given(st.integers(min_value=100, max_value=599))
    def test_invariant_status_code_consistency(self, status_code):
        """Invariant: Status code in response matches returned status"""
        errors = {"validation_errors": {}}
        response, status = BaseValidator.format_error_response(errors, status_code)

        assert response["error"]["code"] == status
        assert status == status_code

    @given(st.data())
    def test_invariant_partial_validation_more_permissive(self, data):
        """Invariant: Partial validation is more permissive than full"""
        # Generate random subset of required fields
        field_data = data.draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(), max_size=5))

        success_full, _, _ = BaseValidator.validate(StrictSchema, field_data, partial=False)
        success_partial, _, _ = BaseValidator.validate(StrictSchema, field_data, partial=True)

        # If full validation succeeds, partial must also succeed
        if success_full:
            assert success_partial


@settings(max_examples=200, deadline=None)
class TestEdgeCaseDiscovery:
    """Use property-based testing to discover edge cases"""

    @given(
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",),  # Exclude surrogates
                blacklist_characters=("\x00",),  # Exclude null
            ),
            max_size=1000,
        )
    )
    def test_unicode_handling(self, text):
        """Test with full Unicode range"""
        data = {"text": text}
        success, validated, errors = BaseValidator.validate(FlexibleSchema, data)

        # Should handle any valid Unicode
        assert isinstance(success, bool)
        if success:
            assert validated["text"] == text

    @given(st.integers(min_value=-(2**63), max_value=2**63 - 1))
    def test_extreme_integer_values(self, number):
        """Test with extreme integer values"""
        data = {"number": number}
        success, validated, errors = BaseValidator.validate(FlexibleSchema, data)

        if success:
            assert validated["number"] == number

    @given(st.lists(st.text(), min_size=0, max_size=100))
    def test_list_size_variations(self, items):
        """Test with various list sizes"""

        class ListSchema(Schema):
            items = fields.List(fields.String())

        data = {"items": items}
        success, validated, errors = BaseValidator.validate(ListSchema, data)

        if success:
            assert len(validated["items"]) == len(items)

    @given(st.recursive(st.integers(), lambda children: st.lists(children, max_size=3), max_leaves=20))
    def test_deeply_nested_structures(self, nested_data):
        """Test with deeply nested data structures"""

        class NestedSchema(Schema):
            data = fields.Raw()

        data = {"data": nested_data}
        success, validated, errors = BaseValidator.validate(NestedSchema, data)

        # Should handle nested structures
        assert isinstance(success, bool)


@settings(max_examples=100, deadline=None)
class TestConcurrencyProperties:
    """Test properties related to concurrent usage"""

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=10, max_size=50))
    def test_property_cache_thread_safety_simulation(self, texts):
        """Simulate concurrent validations (sequential but varied)"""
        results = []

        for text in texts:
            data = {"text": text}
            result = BaseValidator.validate(FlexibleSchema, data)
            results.append(result)

        # All validations should succeed
        assert all(r[0] for r in results)

        # Cache should remain consistent
        assert len(BaseValidator._schema_cache) >= 1


# Stateful testing
try:
    from hypothesis.stateful import RuleBasedStateMachine, rule

    class ValidatorStateMachine(RuleBasedStateMachine):
        """Stateful testing for validator behavior"""

        def __init__(self):
            super().__init__()
            self.validation_count = 0
            self.cache_size_history = []

        @rule(text=st.text(max_size=100))
        def validate_data(self, text):
            """Rule: Validate data and track state"""
            data = {"text": text}
            success, validated, errors = BaseValidator.validate(FlexibleSchema, data)

            self.validation_count += 1
            self.cache_size_history.append(len(BaseValidator._schema_cache))

            # Invariant: Cache doesn't grow unboundedly
            assert len(BaseValidator._schema_cache) <= 10

        @rule()
        def check_cache_stability(self):
            """Rule: Cache size should stabilize"""
            if len(self.cache_size_history) > 5:
                recent = self.cache_size_history[-5:]
                # Cache size should not keep growing
                assert max(recent) - min(recent) <= 2

    TestValidatorStateful = ValidatorStateMachine.TestCase

except ImportError:
    # Stateful testing not available
    pass
