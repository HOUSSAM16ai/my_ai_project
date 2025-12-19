from unittest.mock import MagicMock

from app.services.overmind.planning.base_planner import BasePlanner
from app.services.overmind.planning.fault_tolerance import ResilientPlanner


def test_circuit_breaker_activates():
    """Test that the resilient planner falls back when primary fails."""

    # Define a mock planner class to be used by strategies
    class MockPlannerBase(BasePlanner):
        name = "mock_planner"

        def generate_plan(self, obj, ctx):
            return MagicMock(meta=MagicMock(strategy="mock_success"))

        async def a_generate_plan(self, obj, ctx):
            return MagicMock(meta=MagicMock(strategy="mock_success"))

    # Register the mock planner (it auto-registers on subclassing)
    _ = MockPlannerBase

    # Create failing strategy (simulating a strategy wrapping a broken planner or logic)
    class FailingStrategy:
        name = "failing_strategy"

        def generate(self, obj, ctx):
            raise ValueError("Intentional Failure")

        async def a_generate(self, obj, ctx):
            raise ValueError("Intentional Failure")

    # Create a linear strategy that uses our mock planner
    # We need to mock get_planner_instance to return our MockPlannerBase instance
    # OR we can just inject a mock object if we modify LinearStrategy to accept instance (it currently accepts name)
    # The LinearStrategy looks up planner by name.

    # But wait, LinearStrategy wraps a planner.
    # Let's create a FallbackStrategy that works.

    class WorkingStrategy:
        name = "linear_strategy"

        def generate(self, obj, ctx):
            # Return a simple object with meta attribute
            m = MagicMock()
            m.meta.strategy = "linear_strategy"
            return m

        async def a_generate(self, obj, ctx):
            m = MagicMock()
            m.meta.strategy = "linear_strategy"
            return m

    resilient = ResilientPlanner(
        primary_strategy=FailingStrategy(), fallback_strategy=WorkingStrategy()
    )

    # Run once to trigger failure and fallback
    plan = resilient.generate_safely("Test objective")

    assert plan is not None
    assert plan.meta.strategy == "linear_strategy"
    assert resilient.breaker.failures == 1

    # Run 3 times to open circuit
    resilient.generate_safely("Test 2")
    resilient.generate_safely("Test 3")
    # Total 3 failures now (1 initial + 2 more)
    assert resilient.breaker.failures == 3
    assert resilient.breaker.state == "OPEN"

    # Next run should skip primary immediately
    plan_open = resilient.generate_safely("Test 4")
    assert plan_open.meta.strategy == "linear_strategy"
