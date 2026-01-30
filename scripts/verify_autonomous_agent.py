import asyncio
import sys
from unittest.mock import MagicMock, patch

# Mock dspy to prevent import errors and mock its classes
sys.modules["dspy"] = MagicMock()

# Now import the app modules
from app.services.autonomous_agent.domain.models import AgentStatus, PlanStep
from app.services.autonomous_agent.graph.workflow import create_autonomous_agent_graph


async def run_verification():
    print("Starting Autonomous Agent Verification...")

    # We patch the functions where they are IMPORTED in nodes.py
    with (
        patch("app.services.autonomous_agent.graph.nodes.generate_plan") as mock_plan,
        patch("app.services.autonomous_agent.graph.nodes.decide_action") as mock_decide,
        patch("app.services.autonomous_agent.graph.nodes.reflect_on_work") as mock_reflect,
    ):
        # Scenario: Success after 1 retry
        # 1. Plan: Returns 2 steps
        # On retry, it returns the same plan (simplified for test)
        mock_plan.return_value = [
            PlanStep(id=1, description="Research foundation", status="pending"),
            PlanStep(id=2, description="Pour concrete", status="pending"),
        ]

        # 2. Decide: Always returns a dummy tool
        mock_decide.return_value = ("mock_tool", '{"arg": "test"}')

        # 3. Reflect:
        # First call: REJECTED (Score 5.0)
        # Second call: APPROVED (Score 9.5)
        mock_reflect.side_effect = [
            (5.0, "Foundation too weak.", "REJECTED"),
            (9.5, "Structure is solid.", "APPROVED"),
        ]

        # Build the graph
        graph = create_autonomous_agent_graph()

        # Initial State
        initial_state = {
            "goal": "Build a house",
            "context": {"max_retries": 3},
            "messages": [],
            "plan": [],
            "current_step_index": 0,
            "results": {},
            "retry_count": 0,
            "status": AgentStatus.PENDING,
        }

        print("Invoking Graph...")
        # Run the graph
        result = await graph.ainvoke(initial_state)

        # Debug output
        print("-" * 30)
        print(f"Final Status: {result.get('status')}")
        print(f"Retry Count: {result.get('retry_count')}")
        print(f"Final Score: {result.get('review_score')}")
        print(f"Feedback: {result.get('review_feedback')}")
        print(f"Results: {result.get('results')}")
        print("-" * 30)

        # Assertions
        # 1. Status should be COMPLETED
        if result["status"] != AgentStatus.COMPLETED:
            print("FAILURE: Status is not COMPLETED")
            sys.exit(1)

        # 2. Should have retried once (retry_count == 1)
        if result["retry_count"] != 1:
            print(f"FAILURE: Expected 1 retry, got {result['retry_count']}")
            sys.exit(1)

        # 3. Should have results for steps
        if "step_2" not in result["results"]:
            print("FAILURE: Missing execution results.")
            sys.exit(1)

        print(
            "VERIFICATION SUCCESSFUL: The Agent planned, executed, failed reflection, retried, and succeeded."
        )


if __name__ == "__main__":
    asyncio.run(run_verification())
