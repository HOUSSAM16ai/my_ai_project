
import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass

from app.services.master_agent_service import OvermindService, CandidatePlan
from app.models import Mission, MissionPlan, User, PlanStatus, MissionStatus

# Mocking the schema object
class MockSchema:
    def __init__(self, objective, tasks):
        self.objective = objective
        self.tasks = tasks

@dataclass
class MockTask:
    task_id: str
    description: str
    tool_name: str
    tool_args: dict
    dependencies: list

def test_overmind_persist_plan_logic():
    """
    Verifies that OvermindService._persist_plan correctly constructs the MissionPlan
    with dictionary values for JSON fields, preventing double encoding.
    This unit test mocks the session to inspect the object being persisted.
    """
    # 1. Setup Data
    mission = Mission(id=1, objective="Test Mission", status=MissionStatus.PENDING)

    schema = MockSchema(
        objective="Test Objective",
        tasks=[
            MockTask(
                task_id="t1",
                description="Task 1",
                tool_name="tool1",
                tool_args={"arg": "val"},
                dependencies=[]
            )
        ]
    )

    candidate = CandidatePlan(
        raw=schema,
        planner_name="TestPlanner",
        score=100.0,
        rationale="Because test",
        telemetry={"meta": "data"}
    )

    # 2. Setup Service and Mock Session
    service = OvermindService()
    mock_session = MagicMock()
    # Mock scalar result for version query
    mock_session.scalar.return_value = 0

    # 3. Call the method under test
    service._persist_plan(mission, candidate, 1, mock_session)

    # 4. Verify interactions
    # Check that session.add was called
    # We expect 2 adds: one for MissionPlan, one for Task
    assert mock_session.add.call_count >= 1

    # Extract the MissionPlan object passed to session.add
    # The first call should be for MissionPlan (based on code inspection)
    # But better to find it in the calls
    mission_plan_arg = None
    for call in mock_session.add.call_args_list:
        arg = call[0][0]
        if isinstance(arg, MissionPlan):
            mission_plan_arg = arg
            break

    assert mission_plan_arg is not None, "MissionPlan was not added to session"

    # 5. Assert Correct Types (The Bug Fix Verification)
    print(f"DEBUG: stats_json type: {type(mission_plan_arg.stats_json)}")
    print(f"DEBUG: warnings_json type: {type(mission_plan_arg.warnings_json)}")
    print(f"DEBUG: raw_json type: {type(mission_plan_arg.raw_json)}")

    # Before fix, these were strings. After fix, they must be dict/list.
    assert isinstance(mission_plan_arg.stats_json, dict), "stats_json should be a dict"
    assert isinstance(mission_plan_arg.warnings_json, list), "warnings_json should be a list"
    assert isinstance(mission_plan_arg.raw_json, dict), "raw_json should be a dict"

    # Verify content
    assert mission_plan_arg.stats_json == {}
    assert mission_plan_arg.warnings_json == []
    assert mission_plan_arg.raw_json["objective"] == "Test Objective"
