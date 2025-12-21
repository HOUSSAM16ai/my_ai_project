"""
Tests for Overmind Services (Coverage Gap Fill 2)
=================================================
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Mission,
    MissionEvent,
    MissionStatus,
    Task,
    TaskStatus,
)
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.state import MissionStateManager

# === MissionStateManager Tests ===


class TestMissionStateManager:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def manager(self, mock_session):
        return MissionStateManager(mock_session)

    @pytest.mark.asyncio
    async def test_create_mission(self, manager, mock_session):
        mission = await manager.create_mission("test_obj", 1)
        assert mission.objective == "test_obj"
        assert mission.initiator_id == 1
        assert mission.status == MissionStatus.PENDING
        mock_session.add.assert_called()
        mock_session.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_mission(self, manager, mock_session):
        mock_result = MagicMock()
        mock_mission = Mission(id=1)
        mock_result.scalar_one_or_none.return_value = mock_mission
        mock_session.execute.return_value = mock_result

        m = await manager.get_mission(1)
        assert m == mock_mission
        mock_session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_mission_status(self, manager, mock_session):
        mock_result = MagicMock()
        mock_mission = Mission(id=1, status=MissionStatus.PENDING)
        mock_result.scalar_one_or_none.return_value = mock_mission
        mock_session.execute.return_value = mock_result

        await manager.update_mission_status(1, MissionStatus.RUNNING, "Start")
        assert mock_mission.status == MissionStatus.RUNNING
        mock_session.add.assert_called()  # log_event

    @pytest.mark.asyncio
    async def test_log_event(self, manager, mock_session):
        await manager.log_event(1, "TEST_EVENT", {"data": 1})
        mock_session.add.assert_called()
        # Verify event type matches MissionEvent
        args = mock_session.add.call_args[0]
        assert isinstance(args[0], MissionEvent)

    @pytest.mark.asyncio
    async def test_persist_plan(self, manager, mock_session):
        # Mock version query
        mock_res_ver = MagicMock()
        mock_res_ver.scalar.return_value = 0

        # Mock mission query
        mock_res_mission = MagicMock()
        mock_mission = Mission(id=1)
        mock_res_mission.scalar_one.return_value = mock_mission

        mock_session.execute.side_effect = [mock_res_ver, mock_res_mission]

        mock_plan_schema = MagicMock()
        mock_plan_schema.objective = "obj"
        mock_plan_schema.tasks = [
            MagicMock(
                task_id="t1", description="d1", tool_name="tool", tool_args={}, dependencies=[]
            )
        ]

        mp = await manager.persist_plan(1, "planner", mock_plan_schema, 0.9, "reason")

        assert mp.version == 1
        assert mp.planner_name == "planner"
        assert mock_mission.active_plan_id == mp.id

        # Check task creation
        # We expect 2 adds: Plan and Task
        assert mock_session.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_mark_task_updates(self, manager, mock_session):
        mock_res = MagicMock()
        mock_task = Task(id=1, status=TaskStatus.PENDING, attempt_count=0)
        mock_res.scalar_one.return_value = mock_task
        mock_session.execute.return_value = mock_res

        await manager.mark_task_running(1)
        assert mock_task.status == TaskStatus.RUNNING
        assert mock_task.attempt_count == 1

        await manager.mark_task_complete(1, "done", {})
        assert mock_task.status == TaskStatus.SUCCESS
        assert mock_task.result_text == "done"

        await manager.mark_task_failed(1, "error")
        assert mock_task.status == TaskStatus.FAILED
        assert mock_task.error_text == "error"


# === TaskExecutor Tests ===


class TestTaskExecutor:
    @pytest.mark.asyncio
    async def test_execute_task_no_registry(self):
        # Mock agent_tools import failure behavior
        with patch("app.services.overmind.executor.agent_tools", None):
            executor = TaskExecutor()
            task = Task(tool_name="test")
            res = await executor.execute_task(task)
            assert res["status"] == "failed"
            assert "not available" in res["error"]

    @pytest.mark.asyncio
    async def test_execute_task_tool_not_found(self):
        mock_tools = MagicMock()
        mock_tools._TOOL_REGISTRY = {}
        with patch("app.services.overmind.executor.agent_tools", mock_tools):
            executor = TaskExecutor()
            task = Task(tool_name="unknown")
            res = await executor.execute_task(task)
            assert res["status"] == "failed"
            assert "not found" in res["error"]

    @pytest.mark.asyncio
    async def test_execute_task_success_async(self):
        async def async_tool(arg):
            return f"async-{arg}"

        mock_tools = MagicMock()
        mock_tools._TOOL_REGISTRY = {"my_tool": async_tool}

        with patch("app.services.overmind.executor.agent_tools", mock_tools):
            executor = TaskExecutor()
            task = Task(tool_name="my_tool", tool_args_json={"arg": "val"})
            res = await executor.execute_task(task)
            assert res["status"] == "success"
            assert res["result_text"] == "async-val"

    @pytest.mark.asyncio
    async def test_execute_task_success_sync(self):
        def sync_tool(arg):
            return f"sync-{arg}"

        mock_tools = MagicMock()
        mock_tools._TOOL_REGISTRY = {"my_tool": sync_tool}

        with patch("app.services.overmind.executor.agent_tools", mock_tools):
            executor = TaskExecutor()
            task = Task(tool_name="my_tool", tool_args_json={"arg": "val"})
            res = await executor.execute_task(task)
            assert res["status"] == "success"
            assert res["result_text"] == "sync-val"

    @pytest.mark.asyncio
    async def test_execute_task_exception(self):
        def fail_tool():
            raise ValueError("Boom")

        mock_tools = MagicMock()
        mock_tools._TOOL_REGISTRY = {"fail": fail_tool}

        with patch("app.services.overmind.executor.agent_tools", mock_tools):
            executor = TaskExecutor()
            task = Task(tool_name="fail")
            res = await executor.execute_task(task)
            assert res["status"] == "failed"
            assert "Boom" in res["error"]


# === OvermindOrchestrator Tests ===


class TestOvermindOrchestrator:
    @pytest.fixture
    def mock_state(self):
        return AsyncMock(spec=MissionStateManager)

    @pytest.fixture
    def mock_executor(self):
        return AsyncMock(spec=TaskExecutor)

    @pytest.fixture
    def orchestrator(self, mock_state, mock_executor):
        return OvermindOrchestrator(mock_state, mock_executor)

    @pytest.mark.asyncio
    async def test_run_mission_not_found(self, orchestrator, mock_state):
        mock_state.get_mission.return_value = None
        await orchestrator.run_mission(999)
        # Should exit safely
        mock_state.get_mission.assert_awaited_once_with(999)

    @pytest.mark.asyncio
    async def test_run_mission_catastrophic_failure(self, orchestrator, mock_state):
        mock_state.get_mission.side_effect = Exception("DB Error")
        await orchestrator.run_mission(1)
        mock_state.update_mission_status.assert_awaited()
        # Should log failure

    @pytest.mark.asyncio
    async def test_phase_planning_no_planners(self, orchestrator, mock_state):
        mission = Mission(id=1, status=MissionStatus.PENDING, objective="obj")
        mock_state.get_mission.return_value = mission

        with patch("app.services.overmind.orchestrator.get_all_planners", return_value=[]):
            await orchestrator._phase_planning(mission)
            mock_state.update_mission_status.assert_awaited_with(
                1, MissionStatus.FAILED, "No planners available"
            )

    @pytest.mark.asyncio
    async def test_phase_planning_success(self, orchestrator, mock_state):
        mission = Mission(id=1, status=MissionStatus.PENDING, objective="obj")

        mock_planner = AsyncMock()
        mock_planner.a_instrumented_generate.return_value = {
            "plan": MagicMock(),
            "meta": {"selection_score": 0.9},
        }
        mock_planner.name = "mock_planner"

        with patch("app.services.overmind.orchestrator.get_all_planners", return_value=[mock_planner]):
            await orchestrator._phase_planning(mission)
            mock_state.persist_plan.assert_awaited()
            mock_state.update_mission_status.assert_awaited_with(
                1, MissionStatus.PLANNED, "Plan generated successfully"
            )

    @pytest.mark.asyncio
    async def test_phase_execution_step_all_done(self, orchestrator, mock_state):
        mission = Mission(id=1)
        mock_state.get_tasks.return_value = [
            Task(id=1, status=TaskStatus.SUCCESS),
            Task(id=2, status=TaskStatus.SUCCESS),
        ]

        done = await orchestrator._phase_execution_step(mission)
        assert done is True
        mock_state.update_mission_status.assert_awaited_with(
            1, MissionStatus.SUCCESS, "All tasks completed."
        )

    @pytest.mark.asyncio
    async def test_phase_execution_step_failed(self, orchestrator, mock_state):
        mission = Mission(id=1)
        mock_state.get_tasks.return_value = [Task(id=1, status=TaskStatus.FAILED)]

        done = await orchestrator._phase_execution_step(mission)
        assert done is True
        mock_state.update_mission_status.assert_awaited_with(
            1, MissionStatus.FAILED, "1 tasks failed."
        )

    @pytest.mark.asyncio
    async def test_phase_execution_step_execute_ready(
        self, orchestrator, mock_state, mock_executor
    ):
        mission = Mission(id=1)
        # Task 2 depends on Task 1. Task 1 is Success. Task 2 is Pending.
        t1 = Task(id=1, task_key="t1", status=TaskStatus.SUCCESS)
        t2 = Task(id=2, task_key="t2", status=TaskStatus.PENDING, depends_on_json=["t1"])

        mock_state.get_tasks.return_value = [t1, t2]
        mock_executor.execute_task.return_value = {"status": "success", "result_text": "ok"}

        done = await orchestrator._phase_execution_step(mission)
        assert done is False

        mock_state.mark_task_running.assert_awaited_with(2)
        mock_executor.execute_task.assert_awaited_with(t2)
        mock_state.mark_task_complete.assert_awaited()
