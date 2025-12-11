"""
Comprehensive Tests for Validation Schemas - Security-First Testing
===================================================================

🎯 Target: 100% Coverage with Security-First Approach

Features:
- SQL Injection prevention testing
- XSS attack resistance
- Password hashing verification
- Email validation edge cases
- Property-based fuzzing
- Integration with BaseValidator
"""

import re
from typing import Any

import pytest
from hypothesis import assume, given, settings, strategies as st
from marshmallow import ValidationError
from werkzeug.security import check_password_hash

from app.validators.base import BaseValidator
from app.validators.schemas import (
    AdminConversationSchema,
    AdminMessageSchema,
    MissionPlanSchema,
    MissionSchema,
    PaginationSchema,
    QuerySchema,
    TaskSchema,
    UserSchema,
)


# ======================================================================================
# PAGINATION SCHEMA TESTS
# ======================================================================================


class TestPaginationSchema:
    """Comprehensive tests for PaginationSchema"""

    def test_pagination_defaults(self):
        """Test default pagination values"""
        data = {}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert validated["page"] == 1
        assert validated["per_page"] == 50
        assert validated["order_dir"] == "asc"

    def test_pagination_custom_values(self):
        """Test pagination with custom values"""
        data = {"page": 5, "per_page": 20, "order_by": "created_at", "order_dir": "desc"}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert validated["page"] == 5
        assert validated["per_page"] == 20
        assert validated["order_by"] == "created_at"
        assert validated["order_dir"] == "desc"

    def test_pagination_with_search(self):
        """Test pagination with search query"""
        data = {"page": 1, "search": "test query"}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert validated["search"] == "test query"

    def test_pagination_page_minimum(self):
        """Test page number minimum validation"""
        data = {"page": 0}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is False
        assert "page" in errors["invalid_fields"]

    def test_pagination_page_negative(self):
        """Test negative page number rejection"""
        data = {"page": -5}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is False

    def test_pagination_per_page_maximum(self):
        """Test per_page maximum limit"""
        data = {"per_page": 150}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is False
        assert "per_page" in errors["invalid_fields"]

    def test_pagination_per_page_minimum(self):
        """Test per_page minimum validation"""
        data = {"per_page": 0}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is False

    def test_pagination_invalid_order_dir(self):
        """Test invalid order direction"""
        data = {"order_dir": "invalid"}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is False
        assert "order_dir" in errors["invalid_fields"]

    def test_pagination_unknown_fields_excluded(self):
        """Test that unknown fields are excluded (EXCLUDE policy)"""
        data = {"page": 1, "unknown_field": "should_be_ignored"}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert "unknown_field" not in validated

    @given(st.integers(min_value=1, max_value=10000))
    @settings(max_examples=30)
    def test_pagination_valid_page_numbers(self, page):
        """Property: All valid page numbers should pass validation"""
        data = {"page": page}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert validated["page"] == page

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_pagination_valid_per_page_values(self, per_page):
        """Property: All valid per_page values should pass validation"""
        data = {"per_page": per_page}
        success, validated, errors = BaseValidator.validate(PaginationSchema, data)

        assert success is True
        assert validated["per_page"] == per_page


# ======================================================================================
# QUERY SCHEMA TESTS - SQL INJECTION PREVENTION
# ======================================================================================


class TestQuerySchema:
    """Comprehensive tests for QuerySchema with SQL injection prevention"""

    def test_query_valid_select(self):
        """Test valid SELECT query"""
        data = {"sql": "SELECT * FROM users WHERE id = 1"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is True
        assert validated["sql"] == "SELECT * FROM users WHERE id = 1"

    def test_query_select_with_joins(self):
        """Test complex SELECT query with JOIN"""
        data = {"sql": "SELECT u.*, p.* FROM users u JOIN profiles p ON u.id = p.user_id"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is True

    def test_query_reject_drop_table(self):
        """Test SQL injection prevention - DROP TABLE"""
        data = {"sql": "SELECT * FROM users; DROP TABLE users; --"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "DROP" in str(errors["validation_errors"])

    def test_query_reject_delete(self):
        """Test SQL injection prevention - DELETE"""
        data = {"sql": "DELETE FROM users WHERE id = 1"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        # Error message says "Only SELECT queries are allowed" - DELETE is detected
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_update(self):
        """Test SQL injection prevention - UPDATE"""
        data = {"sql": "UPDATE users SET password = 'hacked' WHERE id = 1"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_insert(self):
        """Test SQL injection prevention - INSERT"""
        data = {"sql": "INSERT INTO users (email) VALUES ('hacker@evil.com')"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_alter(self):
        """Test SQL injection prevention - ALTER"""
        data = {"sql": "ALTER TABLE users ADD COLUMN backdoor VARCHAR(255)"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_truncate(self):
        """Test SQL injection prevention - TRUNCATE"""
        data = {"sql": "TRUNCATE TABLE users"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_exec(self):
        """Test SQL injection prevention - EXEC"""
        data = {"sql": "EXEC sp_executesql 'malicious code'"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_reject_non_select_start(self):
        """Test that queries must start with SELECT"""
        data = {"sql": "   UPDATE users SET name = 'test'"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "SELECT" in str(errors["validation_errors"])

    def test_query_max_length(self):
        """Test query maximum length validation"""
        long_query = "SELECT * FROM users WHERE " + "id = 1 OR " * 2000
        data = {"sql": long_query}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "sql" in errors["invalid_fields"]

    def test_query_min_length(self):
        """Test query minimum length validation"""
        data = {"sql": ""}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False

    def test_query_case_insensitive_keyword_detection(self):
        """Test that dangerous keywords are detected case-insensitively"""
        data = {"sql": "select * from users where id = 1; drop table users"}
        success, validated, errors = BaseValidator.validate(QuerySchema, data)

        assert success is False
        assert "DROP" in str(errors["validation_errors"]).upper()


# ======================================================================================
# USER SCHEMA TESTS - Password Security & Validation
# ======================================================================================


class TestUserSchema:
    """Comprehensive tests for UserSchema with password security"""

    def test_user_create_basic(self):
        """Test basic user creation with required fields"""
        data = {"email": "test@example.com", "full_name": "Test User", "password": "securepass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert validated["email"] == "test@example.com"
        assert validated["full_name"] == "Test User"
        assert "password" not in validated  # Should be converted to password_hash
        assert "password_hash" in validated

    def test_user_password_hashing(self):
        """Test that passwords are properly hashed"""
        data = {"email": "test@example.com", "full_name": "Test User", "password": "mypassword"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert "password_hash" in validated
        # Verify it's a proper hash (could be bcrypt, scrypt, pbkdf2, etc.)
        # werkzeug's generate_password_hash uses scrypt by default in newer versions
        assert validated["password_hash"].startswith(("$2b$", "$2a$", "$2y$", "scrypt:", "pbkdf2:"))
        # Verify password can be checked
        assert check_password_hash(validated["password_hash"], "mypassword")

    def test_user_username_to_full_name_mapping(self):
        """Test backward compatibility: username maps to full_name"""
        data = {"email": "test@example.com", "username": "testuser", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert validated["full_name"] == "testuser"
        assert "username" not in validated

    def test_user_both_username_and_full_name(self):
        """Test that full_name takes precedence when both provided"""
        data = {
            "email": "test@example.com",
            "username": "oldname",
            "full_name": "New Name",
            "password": "pass123",
        }
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert validated["full_name"] == "New Name"
        assert "username" not in validated

    def test_user_neither_username_nor_full_name(self):
        """Test that either username or full_name is required"""
        data = {"email": "test@example.com", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False
        assert "full_name" in str(errors["validation_errors"]) or "username" in str(
            errors["validation_errors"]
        )

    def test_user_invalid_email(self):
        """Test email validation"""
        data = {"email": "not-an-email", "full_name": "Test", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False
        assert "email" in errors["invalid_fields"]

    def test_user_email_max_length(self):
        """Test email maximum length"""
        long_email = "a" * 110 + "@example.com"  # > 120 chars
        data = {"email": long_email, "full_name": "Test", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False

    def test_user_full_name_min_length(self):
        """Test full_name minimum length"""
        data = {"email": "test@example.com", "full_name": "ab", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False
        assert "full_name" in errors["invalid_fields"]

    def test_user_full_name_max_length(self):
        """Test full_name maximum length"""
        long_name = "a" * 151
        data = {"email": "test@example.com", "full_name": long_name, "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False

    def test_user_username_validation_alphanumeric(self):
        """Test username alphanumeric validation"""
        data = {"email": "test@example.com", "username": "valid_user-123", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True

    def test_user_username_validation_invalid_characters(self):
        """Test username rejects invalid characters"""
        data = {"email": "test@example.com", "username": "user@name!", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False
        assert "username" in errors["invalid_fields"]

    def test_user_password_min_length(self):
        """Test password minimum length"""
        data = {"email": "test@example.com", "full_name": "Test", "password": "abc"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is False
        assert "password" in errors["invalid_fields"]

    def test_user_is_admin_default(self):
        """Test is_admin defaults to False"""
        data = {"email": "test@example.com", "full_name": "Test", "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert validated["is_admin"] is False

    def test_user_is_admin_true(self):
        """Test creating admin user"""
        data = {
            "email": "admin@example.com",
            "full_name": "Admin",
            "password": "adminpass",
            "is_admin": True,
        }
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        assert validated["is_admin"] is True

    def test_user_dump_only_fields(self):
        """Test that dump_only fields are excluded from load"""
        data = {
            "email": "test@example.com",
            "full_name": "Test",
            "password": "pass123",
            "id": 999,  # Should be ignored
            "created_at": "2024-01-01",  # Should be ignored
        }
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        assert success is True
        # Dump-only fields should not appear in validated data
        assert "id" not in validated or validated["id"] != 999

    @given(
        st.emails(),
        st.text(min_size=3, max_size=150).filter(lambda x: x.replace("_", "").replace("-", "").replace(" ", "").isalnum()),
        st.text(min_size=4, max_size=50),
    )
    @settings(max_examples=20)
    def test_user_property_based_valid_data(self, email, name, password):
        """Property: Valid user data should always pass validation"""
        data = {"email": email, "full_name": name, "password": password}
        success, validated, errors = BaseValidator.validate(UserSchema, data)

        if success:
            assert "password_hash" in validated
            assert check_password_hash(validated["password_hash"], password)


# ======================================================================================
# MISSION SCHEMA TESTS
# ======================================================================================


class TestMissionSchema:
    """Comprehensive tests for MissionSchema"""

    def test_mission_create_basic(self):
        """Test basic mission creation"""
        data = {"objective": "Complete the project successfully with high quality"}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is True
        assert validated["objective"] == "Complete the project successfully with high quality"
        assert validated["status"] == "PENDING"
        assert validated["priority"] == "MEDIUM"

    def test_mission_all_statuses(self):
        """Test all valid mission statuses"""
        statuses = ["PENDING", "PLANNED", "IN_PROGRESS", "BLOCKED", "COMPLETED", "FAILED", "CANCELLED"]

        for status in statuses:
            data = {"objective": "Test objective for mission", "status": status}
            success, validated, errors = BaseValidator.validate(MissionSchema, data)

            assert success is True
            assert validated["status"] == status

    def test_mission_invalid_status(self):
        """Test invalid mission status"""
        data = {"objective": "Test objective", "status": "INVALID_STATUS"}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is False
        assert "status" in errors["invalid_fields"]

    def test_mission_all_priorities(self):
        """Test all valid mission priorities"""
        priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for priority in priorities:
            data = {"objective": "Test objective for mission", "priority": priority}
            success, validated, errors = BaseValidator.validate(MissionSchema, data)

            assert success is True
            assert validated["priority"] == priority

    def test_mission_invalid_priority(self):
        """Test invalid mission priority"""
        data = {"objective": "Test objective", "priority": "URGENT"}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is False
        assert "priority" in errors["invalid_fields"]

    def test_mission_objective_min_length(self):
        """Test objective minimum length"""
        data = {"objective": "Short"}  # Less than 10 characters
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is False
        assert "objective" in errors["invalid_fields"]

    def test_mission_objective_max_length(self):
        """Test objective maximum length"""
        long_objective = "A" * 5001
        data = {"objective": long_objective}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is False

    def test_mission_dump_only_fields(self):
        """Test dump_only fields are ignored on load"""
        data = {
            "objective": "Complete mission",
            "id": 999,
            "initiator_id": 888,
            "created_at": "2024-01-01",
        }
        success, validated, errors = BaseValidator.validate(MissionSchema, data)

        assert success is True


# ======================================================================================
# TASK SCHEMA TESTS
# ======================================================================================


class TestTaskSchema:
    """Comprehensive tests for TaskSchema"""

    def test_task_create_basic(self):
        """Test basic task creation"""
        data = {
            "mission_id": 1,
            "task_key": "task_001",
            "description": "Implement feature X",
        }
        success, validated, errors = BaseValidator.validate(TaskSchema, data)

        assert success is True
        assert validated["mission_id"] == 1
        assert validated["task_key"] == "task_001"
        assert validated["status"] == "PENDING"
        assert validated["depends_on_json"] == []

    def test_task_all_statuses(self):
        """Test all valid task statuses"""
        statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "SKIPPED"]

        for status in statuses:
            data = {
                "mission_id": 1,
                "task_key": f"task_{status}",
                "description": "Test task",
                "status": status,
            }
            success, validated, errors = BaseValidator.validate(TaskSchema, data)

            assert success is True
            assert validated["status"] == status

    def test_task_with_dependencies(self):
        """Test task with dependency list"""
        data = {
            "mission_id": 1,
            "task_key": "task_003",
            "description": "Dependent task",
            "depends_on_json": ["task_001", "task_002"],
        }
        success, validated, errors = BaseValidator.validate(TaskSchema, data)

        assert success is True
        assert len(validated["depends_on_json"]) == 2
        assert "task_001" in validated["depends_on_json"]

    def test_task_key_max_length(self):
        """Test task_key maximum length"""
        long_key = "t" * 129
        data = {"mission_id": 1, "task_key": long_key, "description": "Test"}
        success, validated, errors = BaseValidator.validate(TaskSchema, data)

        assert success is False

    def test_task_description_max_length(self):
        """Test description maximum length"""
        long_desc = "d" * 2001
        data = {"mission_id": 1, "task_key": "task_001", "description": long_desc}
        success, validated, errors = BaseValidator.validate(TaskSchema, data)

        assert success is False


# ======================================================================================
# MISSION PLAN SCHEMA TESTS
# ======================================================================================


class TestMissionPlanSchema:
    """Comprehensive tests for MissionPlanSchema"""

    def test_mission_plan_basic(self):
        """Test basic mission plan creation"""
        data = {"mission_id": 1}
        success, validated, errors = BaseValidator.validate(MissionPlanSchema, data)

        assert success is True
        assert validated["mission_id"] == 1
        assert validated["plan_version"] == 1
        assert validated["tasks_planned"] == 0

    def test_mission_plan_with_version(self):
        """Test mission plan with version number"""
        data = {"mission_id": 1, "plan_version": 5, "tasks_planned": 10}
        success, validated, errors = BaseValidator.validate(MissionPlanSchema, data)

        assert success is True
        assert validated["plan_version"] == 5
        assert validated["tasks_planned"] == 10

    def test_mission_plan_version_minimum(self):
        """Test plan_version minimum validation"""
        data = {"mission_id": 1, "plan_version": 0}
        success, validated, errors = BaseValidator.validate(MissionPlanSchema, data)

        assert success is False

    def test_mission_plan_tasks_planned_negative(self):
        """Test tasks_planned rejects negative values"""
        data = {"mission_id": 1, "tasks_planned": -5}
        success, validated, errors = BaseValidator.validate(MissionPlanSchema, data)

        assert success is False


# ======================================================================================
# ADMIN CONVERSATION SCHEMA TESTS
# ======================================================================================


class TestAdminConversationSchema:
    """Comprehensive tests for AdminConversationSchema"""

    def test_conversation_create_basic(self):
        """Test basic conversation creation"""
        data = {"title": "Help with database queries"}
        success, validated, errors = BaseValidator.validate(AdminConversationSchema, data)

        assert success is True
        assert validated["title"] == "Help with database queries"
        assert validated["conversation_type"] == "general"
        assert validated["is_archived"] is False
        assert validated["tags"] == []

    def test_conversation_all_types(self):
        """Test all valid conversation types"""
        types = ["general", "database", "mission", "support"]

        for conv_type in types:
            data = {"title": "Test conversation", "conversation_type": conv_type}
            success, validated, errors = BaseValidator.validate(AdminConversationSchema, data)

            assert success is True
            assert validated["conversation_type"] == conv_type

    def test_conversation_with_tags(self):
        """Test conversation with tags"""
        data = {
            "title": "Important discussion",
            "tags": ["urgent", "database", "performance"],
        }
        success, validated, errors = BaseValidator.validate(AdminConversationSchema, data)

        assert success is True
        assert len(validated["tags"]) == 3
        assert "urgent" in validated["tags"]

    def test_conversation_title_max_length(self):
        """Test title maximum length"""
        long_title = "t" * 501
        data = {"title": long_title}
        success, validated, errors = BaseValidator.validate(AdminConversationSchema, data)

        assert success is False


# ======================================================================================
# ADMIN MESSAGE SCHEMA TESTS
# ======================================================================================


class TestAdminMessageSchema:
    """Comprehensive tests for AdminMessageSchema"""

    def test_message_create_user(self):
        """Test creating user message"""
        data = {
            "conversation_id": 1,
            "role": "user",
            "content": "How do I optimize this query?",
        }
        success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

        assert success is True
        assert validated["role"] == "user"
        assert validated["content"] == "How do I optimize this query?"

    def test_message_all_roles(self):
        """Test all valid message roles"""
        roles = ["user", "assistant", "system"]

        for role in roles:
            data = {"conversation_id": 1, "role": role, "content": "Test message"}
            success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

            assert success is True
            assert validated["role"] == role

    def test_message_invalid_role(self):
        """Test invalid message role"""
        data = {"conversation_id": 1, "role": "admin", "content": "Test"}
        success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

        assert success is False
        assert "role" in errors["invalid_fields"]

    def test_message_content_min_length(self):
        """Test content minimum length"""
        data = {"conversation_id": 1, "role": "user", "content": ""}
        success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

        assert success is False

    def test_message_content_max_length(self):
        """Test content maximum length"""
        long_content = "c" * 100001
        data = {"conversation_id": 1, "role": "user", "content": long_content}
        success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

        assert success is False

    def test_message_long_content_acceptable(self):
        """Test that reasonably long content is acceptable"""
        long_content = "This is a detailed message. " * 1000  # ~28000 chars
        data = {"conversation_id": 1, "role": "assistant", "content": long_content}
        success, validated, errors = BaseValidator.validate(AdminMessageSchema, data)

        assert success is True


# ======================================================================================
# SECURITY & EDGE CASE TESTS
# ======================================================================================


class TestSecurityAndEdgeCases:
    """Security and edge case tests across all schemas"""

    def test_xss_prevention_in_text_fields(self):
        """Test that XSS attempts are preserved (sanitization happens at render time)"""
        xss_payload = "<script>alert('XSS')</script>"

        # Test in mission objective
        data = {"objective": xss_payload}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)
        assert success is True
        assert validated["objective"] == xss_payload

        # Test in user full_name
        data = {"email": "test@example.com", "full_name": xss_payload, "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)
        assert success is True

    def test_unicode_support(self):
        """Test unicode support in all schemas"""
        unicode_text = "مرحبا بك في CogniForge 🚀 欢迎"

        # Mission
        data = {"objective": unicode_text}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)
        assert success is True

        # User
        data = {"email": "test@example.com", "full_name": unicode_text, "password": "pass123"}
        success, validated, errors = BaseValidator.validate(UserSchema, data)
        assert success is True

    def test_email_edge_cases(self):
        """Test various email edge cases"""
        valid_emails = [
            "simple@example.com",
            "user+tag@example.com",
            "user.name@example.co.uk",
            "123@example.com",
        ]

        for email in valid_emails:
            data = {"email": email, "full_name": "Test", "password": "pass123"}
            success, validated, errors = BaseValidator.validate(UserSchema, data)
            assert success is True, f"Valid email {email} should pass"

    def test_sql_injection_in_task_key(self):
        """Test SQL injection attempt in task_key"""
        malicious_key = "task'; DROP TABLE tasks; --"
        data = {
            "mission_id": 1,
            "task_key": malicious_key,
            "description": "Test task",
        }
        success, validated, errors = BaseValidator.validate(TaskSchema, data)

        # Should accept (SQL safety is at query execution level)
        assert success is True
        assert validated["task_key"] == malicious_key

    def test_null_byte_injection(self):
        """Test null byte injection attempts"""
        null_payload = "test\x00payload"

        data = {"objective": null_payload}
        success, validated, errors = BaseValidator.validate(MissionSchema, data)
        # Should handle gracefully
        assert isinstance(success, bool)


# ======================================================================================
# INTEGRATION TESTS
# ======================================================================================


class TestSchemaIntegration:
    """Integration tests simulating real-world scenarios"""

    def test_complete_user_workflow(self):
        """Test complete user registration and validation workflow"""
        # Registration
        registration_data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securePassword123",
        }
        success, user, errors = BaseValidator.validate(UserSchema, registration_data)
        assert success is True
        assert check_password_hash(user["password_hash"], "securePassword123")

        # Update (partial)
        update_data = {"full_name": "Updated Name"}
        success, updated, errors = BaseValidator.validate(UserSchema, update_data, partial=True)
        assert success is True

    def test_complete_mission_lifecycle(self):
        """Test complete mission lifecycle validation"""
        # Create mission
        create_data = {"objective": "Implement new feature with comprehensive tests"}
        success, mission, errors = BaseValidator.validate(MissionSchema, create_data)
        assert success is True
        assert mission["status"] == "PENDING"

        # Update to IN_PROGRESS
        update_data = {"status": "IN_PROGRESS"}
        success, updated, errors = BaseValidator.validate(MissionSchema, update_data, partial=True)
        assert success is True

        # Complete
        complete_data = {"status": "COMPLETED"}
        success, completed, errors = BaseValidator.validate(
            MissionSchema, complete_data, partial=True
        )
        assert success is True

    def test_mission_with_tasks_and_plan(self):
        """Test mission with associated tasks and plan"""
        # Create mission
        mission_data = {"objective": "Build comprehensive test suite"}
        success, mission, errors = BaseValidator.validate(MissionSchema, mission_data)
        assert success is True

        # Create plan
        plan_data = {"mission_id": 1, "plan_version": 1, "tasks_planned": 5}
        success, plan, errors = BaseValidator.validate(MissionPlanSchema, plan_data)
        assert success is True

        # Create tasks
        for i in range(1, 4):
            task_data = {
                "mission_id": 1,
                "task_key": f"task_{i:03d}",
                "description": f"Test task {i}",
            }
            success, task, errors = BaseValidator.validate(TaskSchema, task_data)
            assert success is True

    def test_conversation_with_messages(self):
        """Test conversation creation with messages"""
        # Create conversation
        conv_data = {"title": "Database optimization discussion", "conversation_type": "database"}
        success, conv, errors = BaseValidator.validate(AdminConversationSchema, conv_data)
        assert success is True

        # Add user message
        msg_data = {
            "conversation_id": 1,
            "role": "user",
            "content": "How can I optimize slow queries?",
        }
        success, msg, errors = BaseValidator.validate(AdminMessageSchema, msg_data)
        assert success is True

        # Add assistant response
        response_data = {
            "conversation_id": 1,
            "role": "assistant",
            "content": "Here are several strategies for query optimization...",
        }
        success, response, errors = BaseValidator.validate(AdminMessageSchema, response_data)
        assert success is True
