"""
Graph Nodes for the Autonomous Agent.
-------------------------------------
Implements the operational logic for Planning, Executing, and Reflecting.
"""

from typing import Any

from app.core.logging import get_logger
from app.services.autonomous_agent.cognitive.decision import decide_action
from app.services.autonomous_agent.cognitive.planning import generate_plan
from app.services.autonomous_agent.cognitive.reflection import reflect_on_work
from app.services.autonomous_agent.domain.models import (
    AgentStatus,
    AutonomousAgentState,
    WorkResult,
)

logger = get_logger(__name__)


async def planner_node(state: AutonomousAgentState) -> dict[str, Any]:
    """
    Generates the initial plan.
    """
    logger.info("Entering Planner Node")
    goal = state["goal"]
    context = state["context"]

    # Generate plan using DSPy
    steps = generate_plan(goal, context)

    return {"plan": steps, "current_step_index": 0, "status": AgentStatus.EXECUTING, "results": {}}


async def executor_node(state: AutonomousAgentState) -> dict[str, Any]:
    """
    Executes the next step in the plan.
    """
    plan = state["plan"]
    idx = state["current_step_index"]

    # Check if all steps are done
    if idx >= len(plan):
        return {"status": AgentStatus.REFLECTING}

    step = plan[idx]
    logger.info(f"Executing step {idx + 1}: {step.description}")

    # 1. Decide action (Refine high-level step to tool call)
    # For this scaffold, we simulate available tools
    available_tools = "Tools: [web_search(query), calculator(expression), read_file(path)]"
    tool_name, tool_args = decide_action(state["goal"], step.description, available_tools)

    # 2. Execute (Mock execution for the scaffold)
    # In a real scenario, we would resolve the tool and call it.
    output = f"Executed {tool_name} with {tool_args}. Mock Result: Success."

    # 3. Update Step Status
    # We can't mutate the Pydantic object in place if we want to be pure,
    # but strictly LangGraph merges dicts. We need to replace the plan list or update it.
    # To keep it simple, we just store result in 'results'.

    new_results = state.get("results", {}).copy()
    new_results[f"step_{idx + 1}"] = output

    return {"current_step_index": idx + 1, "results": new_results}


async def reflector_node(state: AutonomousAgentState) -> dict[str, Any]:
    """
    Reviews the total work done.
    """
    logger.info("Entering Reflector Node")

    # Aggregate results
    full_outcome = str(state.get("results", {}))
    execution_history = state["plan"]

    score, critique, verdict = reflect_on_work(state["goal"], execution_history, full_outcome)

    logger.info(f"Reflection Verdict: {verdict} (Score: {score})")

    updates = {
        "review_score": score,
        "review_feedback": critique,
        "status": AgentStatus.COMPLETED if verdict == "APPROVED" else AgentStatus.FAILED,
        # Create tentative result
        "final_result": WorkResult(
            status=AgentStatus.COMPLETED if verdict == "APPROVED" else AgentStatus.FAILED,
            outcome=f"Completed with score {score}. Summary: {full_outcome}",
            artifacts={"critique": critique},
            quality_score=score,
        ),
    }

    # Handle retry logic logic is in the graph edges, but we set state here.
    if verdict == "REJECTED":
        # If rejected, we might want to increment retry count
        updates["retry_count"] = state.get("retry_count", 0) + 1

    return updates
