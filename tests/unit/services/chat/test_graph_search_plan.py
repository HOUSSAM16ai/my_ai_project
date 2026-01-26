from unittest.mock import MagicMock

from app.services.chat.graph.search import build_graph_search_plan


def _state_with_message(message: str, user_context: dict | None = None) -> dict:
    return {
        "messages": [MagicMock(content=message)],
        "plan": ["search"],
        "current_step_index": 0,
        "search_results": [],
        "user_context": user_context or {},
        "final_response": "",
        "next": "",
    }


def test_graph_search_plan_includes_base_query() -> None:
    state = _state_with_message("تمارين احتمالات 2024")
    plan = build_graph_search_plan(state)

    assert plan.queries
    assert plan.queries[0] == "تمارين احتمالات 2024"


def test_graph_search_plan_enriches_with_context() -> None:
    state = _state_with_message(
        "تمارين احتمالات",
        {"subject": "رياضيات", "branch": "علوم تجريبية", "year": 2024},
    )
    plan = build_graph_search_plan(state)

    assert any("رياضيات" in query for query in plan.queries)
    assert any("علوم تجريبية" in query for query in plan.queries)
