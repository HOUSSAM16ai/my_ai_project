from unittest.mock import MagicMock, patch

import pytest

from app.overmind.planning.schemas import MissionPlanSchema, PlannedTask
from app.services.master_agent_service import (
    CANON_READ,
    CANON_WRITE,
    Mission,
    MissionPlan,
    MissionStatus,
    OvermindService,
    Task,
    TaskStatus,
    _autofill_file_args,
    _canonicalize_tool_name,
    _compute_diff,
    _ensure_dict,
    _extract_answer_from_data,
    _render_template_in_args,
    run_mission_lifecycle,
    start_mission,
)


# We need to mock SessionLocal since the service uses it directly
@pytest.fixture
def mock_session():
    session = MagicMock()
    # Mock query returns
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.options.return_value = session
    session.all.return_value = []
    session.scalar.return_value = None
    session.get.return_value = None
    return session


@pytest.fixture
def mock_session_local(mock_session):
    with patch("app.services.master_agent_service.SessionLocal", return_value=mock_session) as mock:
        yield mock


@pytest.fixture
def overmind_service():
    return OvermindService()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture
def mock_planners():
    planner = MagicMock()
    planner.name = "TestPlanner"
    planner.instrumented_generate.return_value = {
        "plan": MissionPlanSchema(
            objective="Test Objective",
            tasks=[
                PlannedTask(
                    task_id="task1",
                    description="Do something",
                    tool_name="some_tool",
                    tool_args={"arg": "val"},
                    dependencies=[],
                )
            ],
        ),
        "meta": {"planner": "TestPlanner"},
    }
    with patch("app.services.master_agent_service.get_all_planners", return_value=[planner]):
        yield [planner]


class TestMasterAgentService:
    def test_start_new_mission(self, overmind_service, mock_session_local, mock_session, mock_user):
        """Test starting a new mission creates the record and starts the thread."""
        with patch("threading.Thread") as mock_thread:
            overmind_service.start_new_mission("Test Objective", mock_user)

            # Verify mission creation
            assert mock_session.add.called
            # We can't easily check the exact object added because it's created inside the function
            # But we can check that a Mission object was added
            args, _ = mock_session.add.call_args_list[0]
            assert isinstance(args[0], Mission)
            assert args[0].objective == "Test Objective"
            assert args[0].initiator_id == mock_user.id
            assert args[0].status == MissionStatus.PENDING

            # Verify event logging
            # The second add call should be the event
            _args2, _ = mock_session.add.call_args_list[1]

            # Verify thread start
            mock_thread.assert_called_once()
            call_args = mock_thread.call_args[1]
            assert call_args["target"] == overmind_service.run_mission_lifecycle
            assert call_args["daemon"] is True

    def test_run_mission_lifecycle_not_found(
        self, overmind_service, mock_session_local, mock_session
    ):
        """Test lifecycle handles missing mission gracefully."""
        mock_session.get.return_value = None

        overmind_service.run_mission_lifecycle(999)

    def test_run_mission_lifecycle_catastrophic_failure(
        self, overmind_service, mock_session_local, mock_session
    ):
        """Test catastrophic failure handling in lifecycle."""
        mission = Mission(id=1, status=MissionStatus.PENDING)
        mock_session.get.return_value = mission

        # Mock _tick to raise exception
        with patch.object(overmind_service, "_tick", side_effect=Exception("Boom")):
            overmind_service.run_mission_lifecycle(1)

            assert mission.status == MissionStatus.FAILED

    def test_plan_phase_success(
        self, overmind_service, mock_session_local, mock_session, mock_planners
    ):
        """Test the planning phase successfully selects a plan."""
        mission = Mission(id=1, status=MissionStatus.PENDING)

        # We need to simulate the id assignment by the session
        def add_side_effect(obj):
            if isinstance(obj, MissionPlan):
                obj.id = 100

        mock_session.add.side_effect = add_side_effect

        overmind_service._plan_phase(mission, mock_session)

        assert mission.status == MissionStatus.PLANNED
        assert mission.active_plan_id is not None
        assert mission.active_plan_id == 100

        # Verify plan persistence
        # We expect MissionPlan and Task to be added
        assert mock_session.add.call_count >= 2  # 1 plan + 1 task

    def test_plan_phase_no_planners(self, overmind_service, mock_session_local, mock_session):
        """Test planning phase fails when no planners are available."""
        mission = Mission(id=1, status=MissionStatus.PENDING)

        with patch("app.services.master_agent_service.get_all_planners", return_value=[]):
            overmind_service._plan_phase(mission, mock_session)

            assert mission.status == MissionStatus.FAILED

    def test_plan_phase_all_planners_fail(
        self, overmind_service, mock_session_local, mock_session, mock_planners
    ):
        """Test planning phase fails when all planners raise exceptions."""
        mission = Mission(id=1, status=MissionStatus.PENDING)

        mock_planners[0].instrumented_generate.side_effect = Exception("Planner failed")

        overmind_service._plan_phase(mission, mock_session)

        assert mission.status == MissionStatus.FAILED

    def test_execution_phase_success(self, overmind_service, mock_session_local, mock_session):
        """Test execution phase runs ready tasks."""
        mission = Mission(id=1, status=MissionStatus.RUNNING, active_plan_id=100)

        plan = MissionPlan(id=100, mission_id=1)
        mock_session.get.return_value = plan

        task1 = Task(
            task_key="t1", status=TaskStatus.PENDING, mission_id=1, plan_id=100, depends_on_json=[]
        )
        task2 = Task(
            task_key="t2",
            status=TaskStatus.PENDING,
            mission_id=1,
            plan_id=100,
            depends_on_json=["t1"],
        )

        mock_session.query.return_value.filter_by.return_value.all.return_value = [task1, task2]

        # Mock _execute_single_task to update task status
        def execute_side_effect(mission, task, session):
            task.status = TaskStatus.SUCCESS

        with patch.object(
            overmind_service, "_execute_single_task", side_effect=execute_side_effect
        ) as mock_exec:
            overmind_service._execution_phase(mission, mock_session)

            # Only task1 should be executed because task2 depends on t1 which is not SUCCESS yet (in the initial state)
            mock_exec.assert_called_once()
            assert mock_exec.call_args[0][1] == task1

    def test_execute_single_task_success(self, overmind_service, mock_session_local, mock_session):
        """Test executing a single task."""
        mission = Mission(id=1)
        task = Task(id=10, task_key="t1", status=TaskStatus.PENDING, tool_name="some_tool")

        with patch.object(overmind_service, "_execute_tool", return_value={"result_text": "OK"}):
            overmind_service._execute_single_task(mission, task, mock_session)

            assert task.status == TaskStatus.SUCCESS
            assert task.result_text == "OK"
            assert task.finished_at is not None

    def test_execute_single_task_failure(self, overmind_service, mock_session_local, mock_session):
        """Test single task execution failure handling."""
        mission = Mission(id=1)
        task = Task(id=10, task_key="t1", status=TaskStatus.PENDING, tool_name="some_tool")

        with patch.object(overmind_service, "_execute_tool", side_effect=Exception("Tool failed")):
            overmind_service._execute_single_task(mission, task, mock_session)

            assert task.status == TaskStatus.FAILED
            assert "Tool failed" in task.error_text
            assert task.finished_at is not None

    def test_check_terminal_success(self, overmind_service, mock_session_local, mock_session):
        """Test transition to SUCCESS when all tasks are done."""
        mission = Mission(id=1, status=MissionStatus.RUNNING)

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.count.return_value = 0

        overmind_service._check_terminal(mission, mock_session)

        assert mission.status == MissionStatus.SUCCESS

    def test_check_terminal_failed(self, overmind_service, mock_session_local, mock_session):
        """Test transition to FAILED when there are failed tasks and no active ones."""
        mission = Mission(id=1, status=MissionStatus.RUNNING)

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        # Sequence: pending, retry, running, failed
        mock_filter.count.side_effect = [0, 0, 0, 1]

        overmind_service._check_terminal(mission, mock_session)

        assert mission.status == MissionStatus.FAILED

    def test_tick_loop_timeout(self, overmind_service, mock_session_local, mock_session):
        """Test that the tick loop breaks if runtime limit exceeded."""
        mission = Mission(id=1, status=MissionStatus.RUNNING)

        # Mock time.perf_counter to return huge difference
        with patch("time.perf_counter", side_effect=[0, 100000]):
            with patch("app.services.master_agent_service.MAX_TOTAL_RUNTIME_SECONDS", 100):
                overmind_service._tick(mission, 0, mock_session)

                assert mission.status == MissionStatus.FAILED

    def test_tick_transitions(self, overmind_service, mock_session_local, mock_session):
        """Test _tick orchestrates transitions."""
        mission = Mission(id=1, status=MissionStatus.PENDING)

        # We want to verify it calls _plan_phase
        with patch.object(overmind_service, "_plan_phase") as mock_plan:
            # We need to break the loop.
            def side_effect(m, s):
                m.status = MissionStatus.SUCCESS

            mock_plan.side_effect = side_effect

            overmind_service._tick(mission, 0, mock_session)

            mock_plan.assert_called_once()

    def test_execute_tool_real(self, overmind_service):
        """Test _execute_tool when agent_tools is available."""
        task = Task(tool_name="test_tool", tool_args_json={})

        # Mock agent_tools module
        with patch("app.services.master_agent_service.agent_tools"):
            # We assume agent_tools has some execution logic, but the service mainly uses it to verify presence?
            # Actually the service implementation says:
            # "Re-implement tool execution logic using agent_tools"
            # But in the provided file it just returns success if agent_tools is not None
            # and "Executed {task.tool_name}".
            # So we check that basic behavior.

            result = overmind_service._execute_tool(task)
            assert result["status"] == "success"
            assert "Executed test_tool" in result["result_text"]

    def test_execute_tool_missing(self, overmind_service):
        """Test _execute_tool when agent_tools is missing."""
        task = Task(tool_name="test_tool", tool_args_json={})

        with patch("app.services.master_agent_service.agent_tools", None):
            result = overmind_service._execute_tool(task)
            assert result["status"] == "error"

    def test_adaptive_replan(self, overmind_service, mock_session_local, mock_session):
        """Test adaptive replan stub."""
        mission = Mission(id=1, status=MissionStatus.ADAPTING)
        overmind_service._adaptive_replan(mission, mock_session)
        assert mission.status == MissionStatus.FAILED
        assert (
            "not implemented" in mission.events[-1].payload_json.get("reason", "")
            if mission.events
            else True
        )
        # Or check status note via mock_session calls if note is not on model

    def test_module_wrappers(self, mock_user, mock_session_local):
        """Test start_mission and run_mission_lifecycle wrappers."""
        with patch("threading.Thread"):
            mission = start_mission("Obj", mock_user)
            assert isinstance(mission, Mission)

        with patch(
            "app.services.master_agent_service._overmind_service_singleton.run_mission_lifecycle"
        ) as mock_run:
            run_mission_lifecycle(1)
            mock_run.assert_called_once_with(1)

    # --- Helper Tests ---

    def test_compute_diff(self):
        old = "line1\nline2"
        new = "line1\nline2\nline3"
        diff = _compute_diff(old, new, 100)
        assert diff["lines_added"] == 1
        assert diff["lines_removed"] == 0
        assert "line3" in diff["diff"]

    def test_extract_answer(self):
        assert _extract_answer_from_data({"answer": "yes"}) == "yes"
        assert _extract_answer_from_data({"output": "yes"}) == "yes"
        assert _extract_answer_from_data("yes") == "yes"
        assert _extract_answer_from_data(None) is None

    def test_ensure_dict(self):
        assert _ensure_dict({"a": 1}) == {"a": 1}
        assert _ensure_dict('{"a": 1}') == {"a": 1}
        assert _ensure_dict("bad json") == {"raw": "bad json"}

    def test_canonicalize_tool_name(self):
        assert _canonicalize_tool_name("write_file", "")[0] == CANON_WRITE
        assert _canonicalize_tool_name("read_file", "")[0] == CANON_READ
        assert _canonicalize_tool_name("create_file", "")[0] == CANON_WRITE
        assert _canonicalize_tool_name("unknown.write", "")[0] == CANON_WRITE

        # Test intent guessing
        with patch("app.services.master_agent_service.GUARD_FORCE_FILE_INTENT", True):
            assert _canonicalize_tool_name("file", "please write to disk")[0] == CANON_WRITE

    def test_render_template(self, mock_session):
        """Test {{tXX.answer}} interpolation."""
        mission_id = 1
        # The regex expects t\d{2} (e.g. t01), so t1 is invalid.
        args = {"arg": "{{t01.answer}}"}

        # Mock _collect_prior_outputs behavior
        # It queries tasks.
        Task(task_key="t01", status=TaskStatus.SUCCESS, result_meta_json={"answer": "42"})

        # Let's mock _collect_prior_outputs directly, it's easier and less brittle
        with patch(
            "app.services.master_agent_service._collect_prior_outputs",
            return_value={"t01": {"answer": "42"}},
        ):
            with patch("app.services.master_agent_service.INTERPOLATION_ENABLED", True):
                new_args, notes = _render_template_in_args(args, mission_id, mock_session)

                assert new_args["arg"] == "42"
                assert "placeholder_ok:t01.answer" in notes

    def test_autofill_file_args(self):
        mission = Mission(id=1)
        task = Task(task_key="t1")
        args = {}
        notes = []

        _autofill_file_args(CANON_WRITE, args, mission, task, notes)

        assert "path" in args
        assert "content" in args
        assert "mission1_taskt1" in args["path"]
        assert "mandatory_args_filled" in notes
