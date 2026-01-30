"""
Workflow Construction for the Autonomous Agent.
-----------------------------------------------
Defines the 'Deep Loop' graph: Plan -> Execute -> Reflect -> (Re-Plan).
"""

from langgraph.graph import END, StateGraph

from app.services.autonomous_agent.domain.models import AgentStatus, AutonomousAgentState
from app.services.autonomous_agent.graph.nodes import executor_node, planner_node, reflector_node


def create_autonomous_agent_graph():
    """
    Builds the state graph for the Unit-of-Work agent.
    """
    workflow = StateGraph(AutonomousAgentState)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reflector", reflector_node)

    # Entry Point
    workflow.set_entry_point("planner")

    # Edge: Planner -> Executor
    workflow.add_edge("planner", "executor")

    # Conditional Edge: Executor -> (Executor | Reflector)
    def check_execution_status(state: AutonomousAgentState):
        # If we still have steps to execute, loop back
        if state["current_step_index"] < len(state["plan"]):
            return "continue"
        # Otherwise, reflect on the work
        return "reflect"

    workflow.add_conditional_edges(
        "executor", check_execution_status, {"continue": "executor", "reflect": "reflector"}
    )

    # Conditional Edge: Reflector -> (End | Planner)
    def check_reflection_status(state: AutonomousAgentState):
        status = state.get("status")

        if status == AgentStatus.COMPLETED:
            return "success"

        # If not completed, check retries
        current_retries = state.get("retry_count", 0)
        # Extract max_retries from context or default to 3
        max_retries = state.get("context", {}).get("max_retries", 3)

        if current_retries < max_retries:
            return "retry"

        return "fail"

    workflow.add_conditional_edges(
        "reflector", check_reflection_status, {"success": END, "retry": "planner", "fail": END}
    )

    return workflow.compile()
