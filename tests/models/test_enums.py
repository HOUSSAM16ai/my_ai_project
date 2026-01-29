from app.core.domain.models import (
    MessageRole,
    MissionEventType,
    MissionStatus,
    PlanStatus,
    TaskStatus,
)


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
