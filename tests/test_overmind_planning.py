import pytest
import os
import importlib
from unittest.mock import patch
from app.overmind.planning import base_planner
from app.overmind.planning.base_planner import BasePlanner

class MockPlanner(BasePlanner):
    name = "mock_planner"
    allow_registration = False # prevent registration during testing

def test_base_planner_instantiation():
    planner = MockPlanner()
    assert planner.name == "mock_planner"

def test_base_planner_generate_plan_raises_not_implemented():
    planner = MockPlanner()
    with pytest.raises(NotImplementedError):
        planner.generate_plan("test objective")

@pytest.mark.asyncio
async def test_base_planner_a_generate_plan_raises_not_implemented():
    planner = MockPlanner()
    with pytest.raises(NotImplementedError):
        await planner.a_generate_plan("test objective")

def test_planner_registration():
    class TestPlanner1(BasePlanner):
        name = "test_planner_1"
        allow_registration = True

    class TestPlanner2(BasePlanner):
        name = "test_planner_2"
        allow_registration = True

    class TestPlanner3(BasePlanner):
        name = "test_planner_3"
        allow_registration = False

    assert "test_planner_1" in BasePlanner._registry
    assert "test_planner_2" in BasePlanner._registry
    assert "test_planner_3" not in BasePlanner._registry
    # Cleanup registry for other tests
    BasePlanner._registry.pop("test_planner_1", None)
    BasePlanner._registry.pop("test_planner_2", None)

def test_planner_registration_with_allow_list():
    with patch.dict(os.environ, {"PLANNERS_ALLOW": "allowed_planner"}, clear=True):
        importlib.reload(base_planner)
        class AllowedPlanner(base_planner.BasePlanner):
            name = "allowed_planner"
            allow_registration = True
        class DisallowedPlanner(base_planner.BasePlanner):
            name = "disallowed_planner"
            allow_registration = True
    assert "allowed_planner" in base_planner.BasePlanner._registry
    assert "disallowed_planner" not in base_planner.BasePlanner._registry
    base_planner.BasePlanner._registry.pop("allowed_planner", None)
    importlib.reload(base_planner) # revert to original state

def test_planner_registration_with_block_list():
    with patch.dict(os.environ, {"PLANNERS_BLOCK": "blocked_planner"}, clear=True):
        importlib.reload(base_planner)
        class BlockedPlanner(base_planner.BasePlanner):
            name = "blocked_planner"
            allow_registration = True
        class NormalPlanner(base_planner.BasePlanner):
            name = "normal_planner"
            allow_registration = True
    assert "blocked_planner" not in base_planner.BasePlanner._registry
    assert "normal_planner" in base_planner.BasePlanner._registry
    base_planner.BasePlanner._registry.pop("normal_planner", None)
    importlib.reload(base_planner) # revert to original state
