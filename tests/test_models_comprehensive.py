# tests/test_models_comprehensive.py
"""
Comprehensive tests for the data models (app/models.py).

This module tests critical business logic including:
- Enum case-insensitive lookups (CaseInsensitiveEnum)
- FlexibleEnum TypeDecorator for database storage
- JSONText TypeDecorator for JSON serialization
- User password hashing and verification
- Model relationships and constraints
- Edge cases in data handling
"""

from datetime import UTC, datetime

from app.core.domain.models import (
    AdminConversation,
    AdminMessage,
    FlexibleEnum,
    GeneratedPrompt,
    JSONText,
    MessageRole,
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    PromptTemplate,
    Task,
    TaskStatus,
    User,
    log_mission_event,
    update_mission_status,
    utc_now,
)

# =============================================================================
# UTC NOW HELPER TESTS
# =============================================================================


class TestUtcNow:
    """Tests for the utc_now helper function."""

    def test_returns_datetime(self):
        """utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_returns_utc_timezone(self):
        """utc_now returns datetime with UTC timezone."""
        result = utc_now()
        assert result.tzinfo == UTC

    def test_returns_current_time(self):
        """utc_now returns approximately current time."""
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)
        assert before <= result <= after


# =============================================================================
# CASE INSENSITIVE ENUM TESTS
# =============================================================================


class TestCaseInsensitiveEnum:
    """Tests for CaseInsensitiveEnum base class."""

    def test_lookup_by_uppercase_name(self):
        """Can lookup enum by uppercase name."""
        assert MessageRole["USER"] == MessageRole.USER
        assert MissionStatus["PENDING"] == MissionStatus.PENDING

    def test_lookup_by_lowercase_value(self):
        """Can lookup enum by lowercase value."""
        assert MessageRole("user") == MessageRole.USER
        assert MissionStatus("pending") == MissionStatus.PENDING

    def test_lookup_by_uppercase_value(self):
        """Can lookup enum by uppercase value via _missing_."""
        # The _missing_ method handles case conversion
        assert MessageRole("USER") == MessageRole.USER
        assert MissionStatus("PENDING") == MissionStatus.PENDING

    def test_lookup_by_mixed_case(self):
        """Can lookup enum by mixed case value."""
        assert MessageRole("User") == MessageRole.USER
        assert MissionStatus("Pending") == MissionStatus.PENDING

    def test_invalid_lookup_returns_none(self):
        """Invalid lookup returns None via _missing_."""
        result = MessageRole._missing_("invalid_value")
        assert result is None

    def test_non_string_lookup_returns_none(self):
        """Non-string lookup returns None."""
        result = MessageRole._missing_(123)
        assert result is None


class TestMessageRoleEnum:
    """Tests for MessageRole enum."""

    def test_all_values(self):
        """All MessageRole values are defined."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"
        assert MessageRole.SYSTEM.value == "system"


class TestMissionStatusEnum:
    """Tests for MissionStatus enum."""

    def test_all_values(self):
        """All MissionStatus values are defined."""
        assert MissionStatus.PENDING.value == "pending"
        assert MissionStatus.PLANNING.value == "planning"
        assert MissionStatus.PLANNED.value == "planned"
        assert MissionStatus.RUNNING.value == "running"
        assert MissionStatus.ADAPTING.value == "adapting"
        assert MissionStatus.SUCCESS.value == "success"
        assert MissionStatus.FAILED.value == "failed"
        assert MissionStatus.CANCELED.value == "canceled"


class TestPlanStatusEnum:
    """Tests for PlanStatus enum."""

    def test_all_values(self):
        """All PlanStatus values are defined."""
        assert PlanStatus.DRAFT.value == "draft"
        assert PlanStatus.VALID.value == "valid"
        assert PlanStatus.INVALID.value == "invalid"
        assert PlanStatus.SELECTED.value == "selected"
        assert PlanStatus.ABANDONED.value == "abandoned"


class TestTaskStatusEnum:
    """Tests for TaskStatus enum."""

    def test_all_values(self):
        """All TaskStatus values are defined."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRY.value == "retry"
        assert TaskStatus.SKIPPED.value == "skipped"


class TestMissionEventTypeEnum:
    """Tests for MissionEventType enum."""

    def test_key_values(self):
        """Key MissionEventType values are defined."""
        assert MissionEventType.CREATED.value == "mission_created"
        assert MissionEventType.EXECUTION_STARTED.value == "execution_started"
        assert MissionEventType.TASK_STARTED.value == "task_started"
        assert MissionEventType.MISSION_COMPLETED.value == "mission_completed"
        assert MissionEventType.MISSION_FAILED.value == "mission_failed"


# =============================================================================
# FLEXIBLE ENUM TYPE DECORATOR TESTS
# =============================================================================


class TestFlexibleEnum:
    """Tests for FlexibleEnum TypeDecorator."""

    def test_process_bind_param_with_enum(self):
        """Binding an enum stores its value."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param(MessageRole.USER, None)
        assert result == "user"

    def test_process_bind_param_with_string(self):
        """Binding a string normalizes to enum value."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param("USER", None)
        assert result == "user"

    def test_process_bind_param_with_none(self):
        """Binding None returns None."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_bind_param(None, None)
        assert result is None

    def test_process_result_value_returns_enum(self):
        """Result value is converted to enum."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value("user", None)
        assert result == MessageRole.USER

    def test_process_result_value_case_insensitive(self):
        """Result value handles case insensitively."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value("USER", None)
        assert result == MessageRole.USER

    def test_process_result_value_with_none(self):
        """Result value None returns None."""
        decorator = FlexibleEnum(MessageRole)
        result = decorator.process_result_value(None, None)
        assert result is None


# =============================================================================
# JSON TEXT TYPE DECORATOR TESTS
# =============================================================================


class TestJSONText:
    """Tests for JSONText TypeDecorator."""

    def test_process_bind_param_with_dict(self):
        """Binding a dict serializes to JSON string."""
        decorator = JSONText()
        data = {"key": "value", "number": 42}
        result = decorator.process_bind_param(data, None)
        assert result == '{"key": "value", "number": 42}'

    def test_process_bind_param_with_list(self):
        """Binding a list serializes to JSON string."""
        decorator = JSONText()
        data = [1, 2, 3, "four"]
        result = decorator.process_bind_param(data, None)
        assert result == '[1, 2, 3, "four"]'

    def test_process_bind_param_with_none(self):
        """Binding None returns None."""
        decorator = JSONText()
        result = decorator.process_bind_param(None, None)
        assert result is None

    def test_process_bind_param_with_primitive(self):
        """Binding primitives serializes correctly."""
        decorator = JSONText()
        assert decorator.process_bind_param(42, None) == "42"
        assert decorator.process_bind_param(True, None) == "true"
        assert decorator.process_bind_param("string", None) == '"string"'

    def test_process_result_value_with_dict(self):
        """Result value deserializes dict from JSON."""
        decorator = JSONText()
        result = decorator.process_result_value('{"key": "value"}', None)
        assert result == {"key": "value"}

    def test_process_result_value_with_list(self):
        """Result value deserializes list from JSON."""
        decorator = JSONText()
        result = decorator.process_result_value("[1, 2, 3]", None)
        assert result == [1, 2, 3]

    def test_process_result_value_with_none(self):
        """Result value None returns None."""
        decorator = JSONText()
        result = decorator.process_result_value(None, None)
        assert result is None

    def test_process_result_value_with_invalid_json(self):
        """Result value returns raw value on JSON decode error."""
        decorator = JSONText()
        result = decorator.process_result_value("not valid json {", None)
        assert result == "not valid json {"

    def test_roundtrip_complex_data(self):
        """Complex data survives roundtrip through JSONText."""
        decorator = JSONText()
        data = {
            "nested": {"a": 1, "b": [2, 3]},
            "array": [{"x": 1}, {"y": 2}],
            "null": None,
            "bool": True,
        }
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data


# =============================================================================
# USER MODEL TESTS
# =============================================================================


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """User can be created with required fields."""
        user = User(full_name="Test User", email="test@example.com")
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
        assert user.is_admin is False
        assert user.password_hash is None

    def test_set_password(self):
        """set_password hashes the password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("secure_password_123")
        assert user.password_hash is not None
        assert user.password_hash != "secure_password_123"
        assert len(user.password_hash) > 20

    def test_check_password_correct(self):
        """check_password returns True for correct password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.check_password("my_password") is True

    def test_check_password_incorrect(self):
        """check_password returns False for incorrect password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.check_password("wrong_password") is False

    def test_check_password_no_hash(self):
        """check_password returns False when no hash is set."""
        user = User(full_name="Test", email="test@example.com")
        assert user.check_password("any_password") is False

    def test_verify_password_alias(self):
        """verify_password is an alias for check_password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.verify_password("my_password") is True
        assert user.verify_password("wrong") is False

    def test_user_repr(self):
        """User has meaningful repr."""
        user = User(id=1, full_name="Test", email="test@example.com")
        repr_str = repr(user)
        assert "User" in repr_str
        assert "1" in repr_str
        assert "test@example.com" in repr_str

    def test_password_hashing_uses_argon2(self):
        """Password hashing prefers Argon2."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("test123")
        # Argon2 hashes start with $argon2
        assert user.password_hash.startswith("$argon2")


# =============================================================================
# ADMIN CONVERSATION MODEL TESTS
# =============================================================================


class TestAdminConversationModel:
    """Tests for AdminConversation model."""

    def test_conversation_creation(self):
        """AdminConversation can be created with required fields."""
        conv = AdminConversation(title="Test Conversation", user_id=1)
        assert conv.title == "Test Conversation"
        assert conv.user_id == 1
        assert conv.conversation_type == "general"

    def test_conversation_custom_type(self):
        """AdminConversation can have custom type."""
        conv = AdminConversation(title="Debug Session", user_id=1, conversation_type="debug")
        assert conv.conversation_type == "debug"


# =============================================================================
# ADMIN MESSAGE MODEL TESTS
# =============================================================================


class TestAdminMessageModel:
    """Tests for AdminMessage model."""

    def test_message_creation(self):
        """AdminMessage can be created with required fields."""
        msg = AdminMessage(conversation_id=1, role=MessageRole.USER, content="Hello, world!")
        assert msg.conversation_id == 1
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"

    def test_message_with_all_roles(self):
        """AdminMessage supports all MessageRole values."""
        for role in MessageRole:
            msg = AdminMessage(conversation_id=1, role=role, content="Test")
            assert msg.role == role


# =============================================================================
# MISSION MODEL TESTS
# =============================================================================


class TestMissionModel:
    """Tests for Mission model."""

    def test_mission_creation(self):
        """Mission can be created with required fields."""
        mission = Mission(objective="Build a feature", initiator_id=1)
        assert mission.objective == "Build a feature"
        assert mission.initiator_id == 1
        assert mission.status == MissionStatus.PENDING

    def test_mission_default_status(self):
        """Mission defaults to PENDING status."""
        mission = Mission(objective="Test", initiator_id=1)
        assert mission.status == MissionStatus.PENDING


# =============================================================================
# MISSION PLAN MODEL TESTS
# =============================================================================


class TestMissionPlanModel:
    """Tests for MissionPlan model."""

    def test_plan_creation(self):
        """MissionPlan can be created with required fields."""
        plan = MissionPlan(mission_id=1, planner_name="test_planner")
        assert plan.mission_id == 1
        assert plan.planner_name == "test_planner"
        assert plan.status == PlanStatus.DRAFT
        assert plan.version == 1
        assert plan.score == 0.0

    def test_plan_json_fields(self):
        """MissionPlan JSON fields work correctly."""
        plan = MissionPlan(
            mission_id=1,
            planner_name="test",
            raw_json={"key": "value"},
            stats_json={"count": 10},
            warnings_json=["warning1", "warning2"],
        )
        assert plan.raw_json == {"key": "value"}
        assert plan.stats_json == {"count": 10}
        assert plan.warnings_json == ["warning1", "warning2"]


# =============================================================================
# TASK MODEL TESTS
# =============================================================================


class TestTaskModel:
    """Tests for Task model."""

    def test_task_creation(self):
        """Task can be created with required fields."""
        task = Task(mission_id=1, task_key="task_1")
        assert task.mission_id == 1
        assert task.task_key == "task_1"
        assert task.status == TaskStatus.PENDING
        assert task.attempt_count == 0
        assert task.max_attempts == 3

    def test_task_json_fields(self):
        """Task JSON fields work correctly."""
        task = Task(
            mission_id=1,
            task_key="task_1",
            tool_args_json={"arg1": "value1"},
            depends_on_json=["task_0"],
            result_meta_json={"success": True},
        )
        assert task.tool_args_json == {"arg1": "value1"}
        assert task.depends_on_json == ["task_0"]
        assert task.result_meta_json == {"success": True}


# =============================================================================
# MISSION EVENT MODEL TESTS
# =============================================================================


class TestMissionEventModel:
    """Tests for MissionEvent model."""

    def test_event_creation(self):
        """MissionEvent can be created with required fields."""
        event = MissionEvent(
            mission_id=1,
            event_type=MissionEventType.CREATED,
            payload_json={"info": "Mission started"},
        )
        assert event.mission_id == 1
        assert event.event_type == MissionEventType.CREATED
        assert event.payload_json == {"info": "Mission started"}


# =============================================================================
# PROMPT TEMPLATE MODEL TESTS
# =============================================================================


class TestPromptTemplateModel:
    """Tests for PromptTemplate model."""

    def test_template_creation(self):
        """PromptTemplate can be created with required fields."""
        template = PromptTemplate(name="greeting", template="Hello, {name}!")
        assert template.name == "greeting"
        assert template.template == "Hello, {name}!"


# =============================================================================
# GENERATED PROMPT MODEL TESTS
# =============================================================================


class TestGeneratedPromptModel:
    """Tests for GeneratedPrompt model."""

    def test_prompt_creation(self):
        """GeneratedPrompt can be created with required fields."""
        prompt = GeneratedPrompt(prompt="Hello, World!", template_id=1)
        assert prompt.prompt == "Hello, World!"
        assert prompt.template_id == 1


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestLogMissionEvent:
    """Tests for log_mission_event helper."""

    def test_creates_event_without_session(self):
        """log_mission_event creates event without session."""
        mission = Mission(id=1, objective="Test", initiator_id=1)
        # Should not raise even without session
        log_mission_event(mission, MissionEventType.CREATED, {"detail": "test"}, session=None)


class TestUpdateMissionStatus:
    """Tests for update_mission_status helper."""

    def test_updates_status(self):
        """update_mission_status changes mission status."""
        mission = Mission(id=1, objective="Test", initiator_id=1, status=MissionStatus.PENDING)
        old_updated_at = mission.updated_at

        update_mission_status(mission, MissionStatus.RUNNING)

        assert mission.status == MissionStatus.RUNNING
        assert mission.updated_at >= old_updated_at


# =============================================================================
# PASSWORD HASHING EDGE CASES
# =============================================================================


class TestPasswordHashingEdgeCases:
    """Edge case tests for password hashing."""

    def test_empty_password(self):
        """Empty password can be hashed and verified."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("")
        assert user.check_password("") is True
        assert user.check_password("not_empty") is False

    def test_unicode_password(self):
        """Unicode characters in password work correctly."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("كلمة_سر_قوية_🔐")
        assert user.check_password("كلمة_سر_قوية_🔐") is True
        assert user.check_password("wrong") is False

    def test_very_long_password(self):
        """Very long passwords work correctly."""
        user = User(full_name="Test", email="test@example.com")
        long_password = "a" * 1000
        user.set_password(long_password)
        assert user.check_password(long_password) is True

    def test_special_characters_password(self):
        """Special characters in password work correctly."""
        user = User(full_name="Test", email="test@example.com")
        special_password = "p@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        user.set_password(special_password)
        assert user.check_password(special_password) is True


# =============================================================================
# JSONTEXT EDGE CASES
# =============================================================================


class TestJSONTextEdgeCases:
    """Edge case tests for JSONText TypeDecorator."""

    def test_empty_dict(self):
        """Empty dict survives roundtrip."""
        decorator = JSONText()
        serialized = decorator.process_bind_param({}, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == {}

    def test_empty_list(self):
        """Empty list survives roundtrip."""
        decorator = JSONText()
        serialized = decorator.process_bind_param([], None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == []

    def test_unicode_in_json(self):
        """Unicode data survives roundtrip."""
        decorator = JSONText()
        data = {"arabic": "مرحبا", "emoji": "🚀", "chinese": "你好"}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data

    def test_nested_null_values(self):
        """Nested null values survive roundtrip."""
        decorator = JSONText()
        data = {"a": None, "b": {"c": None}}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data

    def test_large_json(self):
        """Large JSON data survives roundtrip."""
        decorator = JSONText()
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}
        serialized = decorator.process_bind_param(data, None)
        deserialized = decorator.process_result_value(serialized, None)
        assert deserialized == data
        assert len(deserialized["items"]) == 1000
