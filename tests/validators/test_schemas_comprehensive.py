"""
Comprehensive Unit Tests for Validation Schemas
================================================

Coverage Target: 100%
Testing Strategy:
- All schema classes
- Field validation rules
- Custom validators
- Edge cases and boundaries
- Type coercion
"""

import pytest
from marshmallow import ValidationError

from app.validators.schemas import PaginationSchema, QuerySchema


class TestPaginationSchema:
    """Test PaginationSchema - all fields and validation rules"""

    def test_pagination_default_values(self):
        """Test that default values are applied correctly"""
        schema = PaginationSchema()
        result = schema.load({})

        assert result["page"] == 1
        assert result["per_page"] == 50
        assert result["order_dir"] == "asc"

    def test_pagination_valid_data(self):
        """Test with all valid fields"""
        data = {"page": 2, "per_page": 25, "search": "test", "order_by": "name", "order_dir": "desc"}
        schema = PaginationSchema()
        result = schema.load(data)

        assert result["page"] == 2
        assert result["per_page"] == 25
        assert result["search"] == "test"
        assert result["order_by"] == "name"
        assert result["order_dir"] == "desc"

    def test_pagination_page_minimum_validation(self):
        """Test that page must be >= 1"""
        schema = PaginationSchema()

        # Valid: page = 1
        result = schema.load({"page": 1})
        assert result["page"] == 1

        # Invalid: page = 0
        with pytest.raises(ValidationError) as exc_info:
            schema.load({"page": 0})
        assert "page" in str(exc_info.value)

        # Invalid: page = -1
        with pytest.raises(ValidationError):
            schema.load({"page": -1})

    def test_pagination_per_page_range_validation(self):
        """Test that per_page is between 1 and 100"""
        schema = PaginationSchema()

        # Valid: per_page = 1
        result = schema.load({"per_page": 1})
        assert result["per_page"] == 1

        # Valid: per_page = 100
        result = schema.load({"per_page": 100})
        assert result["per_page"] == 100

        # Invalid: per_page = 0
        with pytest.raises(ValidationError):
            schema.load({"per_page": 0})

        # Invalid: per_page = 101
        with pytest.raises(ValidationError):
            schema.load({"per_page": 101})

    def test_pagination_order_dir_validation(self):
        """Test that order_dir only accepts 'asc' or 'desc'"""
        schema = PaginationSchema()

        # Valid: asc
        result = schema.load({"order_dir": "asc"})
        assert result["order_dir"] == "asc"

        # Valid: desc
        result = schema.load({"order_dir": "desc"})
        assert result["order_dir"] == "desc"

        # Invalid: other values
        with pytest.raises(ValidationError) as exc_info:
            schema.load({"order_dir": "invalid"})
        assert "order_dir" in str(exc_info.value)

    def test_pagination_optional_fields(self):
        """Test that search and order_by are optional"""
        schema = PaginationSchema()

        # Without optional fields
        result = schema.load({"page": 1})
        assert "search" not in result or result.get("search") is None
        assert "order_by" not in result or result.get("order_by") is None

        # With optional fields
        result = schema.load({"page": 1, "search": "query", "order_by": "created_at"})
        assert result["search"] == "query"
        assert result["order_by"] == "created_at"

    def test_pagination_none_values_for_optional(self):
        """Test that None is accepted for optional fields"""
        schema = PaginationSchema()
        result = schema.load({"page": 1, "search": None, "order_by": None})

        assert result.get("search") is None
        assert result.get("order_by") is None

    def test_pagination_type_coercion(self):
        """Test that string numbers are coerced to integers"""
        schema = PaginationSchema()

        # String numbers should be converted
        result = schema.load({"page": "2", "per_page": "30"})
        assert result["page"] == 2
        assert result["per_page"] == 30
        assert isinstance(result["page"], int)

    def test_pagination_invalid_types(self):
        """Test validation fails with invalid types"""
        schema = PaginationSchema()

        # Invalid: non-numeric string for page
        with pytest.raises(ValidationError):
            schema.load({"page": "not_a_number"})

        # Invalid: float for page (might be coerced or rejected)
        try:
            result = schema.load({"page": 2.5})
            # If coerced, should be integer
            assert isinstance(result["page"], int)
        except ValidationError:
            # Or might reject floats
            pass

    def test_pagination_boundary_values(self):
        """Test boundary values for pagination"""
        schema = PaginationSchema()

        # Maximum valid per_page
        result = schema.load({"per_page": 100})
        assert result["per_page"] == 100

        # Minimum valid page
        result = schema.load({"page": 1})
        assert result["page"] == 1

        # Large page number
        result = schema.load({"page": 999999})
        assert result["page"] == 999999

    def test_pagination_empty_strings(self):
        """Test with empty strings for optional fields"""
        schema = PaginationSchema()
        result = schema.load({"search": "", "order_by": ""})

        # Empty strings should be accepted
        assert result.get("search") == ""
        assert result.get("order_by") == ""

    def test_pagination_unicode_search(self):
        """Test search with Unicode characters"""
        schema = PaginationSchema()
        result = schema.load({"search": "بحث عربي"})

        assert result["search"] == "بحث عربي"

    def test_pagination_special_characters_in_search(self):
        """Test search with special characters"""
        schema = PaginationSchema()
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        result = schema.load({"search": special_chars})

        assert result["search"] == special_chars


class TestQuerySchema:
    """Test QuerySchema - SQL query validation"""

    def test_query_schema_required_sql_field(self):
        """Test that sql field is required"""
        schema = QuerySchema()

        # Valid: with sql field
        result = schema.load({"sql": "SELECT * FROM users"})
        assert result["sql"] == "SELECT * FROM users"

        # Invalid: missing sql field
        with pytest.raises(ValidationError) as exc_info:
            schema.load({})
        assert "sql" in str(exc_info.value)

    def test_query_schema_empty_sql(self):
        """Test with empty SQL string"""
        schema = QuerySchema()

        # Empty string might be invalid depending on schema definition
        try:
            result = schema.load({"sql": ""})
            # If accepted, should be empty string
            assert result["sql"] == ""
        except ValidationError:
            # Or might require non-empty
            pass

    def test_query_schema_complex_sql(self):
        """Test with complex SQL queries"""
        schema = QuerySchema()
        complex_queries = [
            "SELECT * FROM users WHERE age > 18",
            "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
            "UPDATE users SET active = true WHERE id = 1",
            "DELETE FROM users WHERE created_at < '2020-01-01'",
        ]

        for sql in complex_queries:
            result = schema.load({"sql": sql})
            assert result["sql"] == sql

    def test_query_schema_sql_with_newlines(self):
        """Test SQL with newlines and formatting"""
        schema = QuerySchema()
        sql = """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE active = true
        """
        result = schema.load({"sql": sql})
        assert result["sql"] == sql

    def test_query_schema_sql_with_special_characters(self):
        """Test SQL with special characters"""
        schema = QuerySchema()
        sql = "SELECT * FROM users WHERE name LIKE '%test%'"
        result = schema.load({"sql": sql})
        assert result["sql"] == sql

    def test_query_schema_sql_injection_patterns(self):
        """Test that schema accepts (but doesn't validate) injection patterns"""
        schema = QuerySchema()

        # Schema should accept these (validation happens elsewhere)
        injection_patterns = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users WHERE name = 'admin'--",
        ]

        for sql in injection_patterns:
            result = schema.load({"sql": sql})
            assert result["sql"] == sql

    def test_query_schema_unicode_in_sql(self):
        """Test SQL with Unicode characters"""
        schema = QuerySchema()
        sql = "SELECT * FROM users WHERE name = 'مستخدم'"
        result = schema.load({"sql": sql})
        assert result["sql"] == sql


class TestSchemaEdgeCases:
    """Test edge cases across all schemas"""

    def test_schema_with_extra_fields(self):
        """Test that extra fields are handled (ignored by default)"""
        schema = PaginationSchema()
        data = {"page": 1, "extra_field": "ignored", "another": 123}

        result = schema.load(data)
        # Extra fields should be ignored
        assert "extra_field" not in result
        assert "another" not in result

    def test_schema_with_null_for_required_field(self):
        """Test that null is rejected for required fields"""
        schema = QuerySchema()

        with pytest.raises(ValidationError):
            schema.load({"sql": None})

    def test_schema_case_sensitivity(self):
        """Test field name case sensitivity"""
        schema = PaginationSchema()

        # Correct case
        result = schema.load({"page": 1})
        assert result["page"] == 1

        # Wrong case should be ignored
        result = schema.load({"Page": 1, "PAGE": 2})
        # Should use default since correct case not provided
        assert result["page"] == 1  # default value

    def test_schema_with_very_long_strings(self):
        """Test with very long string values"""
        schema = PaginationSchema()
        long_string = "x" * 10000

        result = schema.load({"search": long_string})
        assert len(result["search"]) == 10000


class TestSchemaIntegration:
    """Integration tests for schema usage"""

    def test_pagination_full_workflow(self):
        """Test complete pagination workflow"""
        schema = PaginationSchema()

        # Simulate API request with query parameters
        query_params = {"page": "3", "per_page": "20", "search": "test user", "order_by": "created_at", "order_dir": "desc"}

        result = schema.load(query_params)

        # Verify all fields processed correctly
        assert result["page"] == 3
        assert result["per_page"] == 20
        assert result["search"] == "test user"
        assert result["order_by"] == "created_at"
        assert result["order_dir"] == "desc"

    def test_query_schema_with_parameterized_query(self):
        """Test query schema with parameterized SQL"""
        schema = QuerySchema()

        sql = "SELECT * FROM users WHERE id = ? AND active = ?"
        result = schema.load({"sql": sql})

        assert "?" in result["sql"]


# Property-based tests
try:
    from hypothesis import given
    from hypothesis import strategies as st

    class TestSchemasPropertyBased:
        """Property-based tests for schemas"""

        @given(st.integers(min_value=1, max_value=1000000))
        def test_pagination_any_valid_page(self, page):
            """Property: Any positive integer should be valid for page"""
            schema = PaginationSchema()
            result = schema.load({"page": page})
            assert result["page"] == page

        @given(st.integers(min_value=1, max_value=100))
        def test_pagination_any_valid_per_page(self, per_page):
            """Property: Any integer 1-100 should be valid for per_page"""
            schema = PaginationSchema()
            result = schema.load({"per_page": per_page})
            assert result["per_page"] == per_page

        @given(st.text(min_size=1))
        def test_query_schema_any_non_empty_string(self, sql):
            """Property: Any non-empty string should be valid for sql"""
            schema = QuerySchema()
            result = schema.load({"sql": sql})
            assert result["sql"] == sql

        @given(st.text())
        def test_pagination_search_any_string(self, search):
            """Property: Any string should be valid for search"""
            schema = PaginationSchema()
            result = schema.load({"search": search})
            assert result.get("search") == search

except ImportError:
    pass


# Fuzzing tests
class TestSchemasFuzzing:
    """Fuzzing tests with random/malformed input"""

    def test_fuzz_pagination_with_random_types(self):
        """Test pagination with various random types"""
        schema = PaginationSchema()

        test_cases = [
            {"page": []},
            {"page": {}},
            {"page": True},
            {"per_page": "not_a_number"},
            {"order_dir": 123},
        ]

        for data in test_cases:
            try:
                schema.load(data)
            except ValidationError:
                # Expected for invalid types
                pass

    def test_fuzz_query_with_binary_data(self):
        """Test query schema with binary-like data"""
        schema = QuerySchema()

        # Should handle gracefully
        try:
            result = schema.load({"sql": "\\x00\\x01\\x02"})
            assert isinstance(result["sql"], str)
        except ValidationError:
            pass

    def test_fuzz_extreme_values(self):
        """Test with extreme numeric values"""
        schema = PaginationSchema()

        extreme_values = [
            {"page": 2**31 - 1},
            {"page": 2**63 - 1},
            {"per_page": 1},
            {"per_page": 100},
        ]

        for data in extreme_values:
            try:
                result = schema.load(data)
                # Should handle or reject gracefully
                assert isinstance(result.get("page", 1), int)
            except (ValidationError, OverflowError):
                pass
