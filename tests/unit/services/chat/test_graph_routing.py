from unittest.mock import MagicMock

from app.services.chat.graph.routing import determine_next_node


def _base_state() -> dict:
    return {
        "messages": [MagicMock(content="مرحبا")],
        "plan": [],
        "current_step_index": 0,
        "search_results": [],
        "user_context": {},
        "final_response": "",
        "next": "",
    }


def test_routing_prefers_planner_when_plan_missing() -> None:
    state = _base_state()
    next_node, trace = determine_next_node(state)
    assert next_node == "planner"
    assert trace


def test_routing_skips_search_when_results_available() -> None:
    state = _base_state()
    state["plan"] = ["search", "explain"]
    state["search_results"] = [{"content": "نتيجة"}]

    next_node, _ = determine_next_node(state)
    assert next_node == "writer"


def test_routing_respects_reasoning_signal() -> None:
    state = _base_state()
    state["plan"] = ["search", "explain"]
    state["messages"] = [MagicMock(content="برهن صحة النتيجة")]

    next_node, _ = determine_next_node(state)
    assert next_node == "super_reasoner"
