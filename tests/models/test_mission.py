from app.core.domain.models import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    Task,
    TaskStatus,
    log_mission_event,
    update_mission_status,
)


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
