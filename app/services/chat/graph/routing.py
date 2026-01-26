"""
توجيه الرسم البياني (Graph Routing Intelligence).
-------------------------------------------------
يوفر هذا الملف خوارزميات قرار ذكية لتحديد العقدة التالية
بناءً على إشارات السياق وخطة التنفيذ الحالية.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.graph.state import AgentState


@dataclass(frozen=True)
class RoutingPolicy:
    """سياسة توجيه قابلة للضبط عبر بيانات واضحة."""

    base_scores: dict[str, float]
    boosts: dict[str, dict[str, float]]


_DEFAULT_POLICY = RoutingPolicy(
    base_scores={
        "planner": 0.0,
        "researcher": 0.0,
        "super_reasoner": 0.0,
        "writer": 0.0,
        "end": -10.0,
    },
    boosts={
        "missing_plan": {"planner": 10.0},
        "plan_exhausted": {"end": 15.0},
        "step_search": {"researcher": 6.0},
        "step_reason": {"super_reasoner": 6.0},
        "step_explain": {"writer": 6.0},
        "step_analyze": {"writer": 4.0},
        "has_search_results": {"writer": 8.0},
        "needs_reasoning": {"super_reasoner": 8.0},
    },
)


def determine_next_node(
    state: AgentState, policy: RoutingPolicy = _DEFAULT_POLICY
) -> tuple[str, list[dict[str, object]]]:
    """
    يحدد العقدة التالية بناءً على إشارات السياق مع تسجيل أثر القرار.
    """
    plan = state.get("plan", [])
    idx = state.get("current_step_index", 0)
    signals = _extract_signals(state, plan, idx)

    scores = dict(policy.base_scores)
    trace: list[dict[str, object]] = []
    for signal, active in signals.items():
        if not active:
            continue
        for node_name, boost in policy.boosts.get(signal, {}).items():
            scores[node_name] = scores.get(node_name, 0.0) + boost
            trace.append({"signal": signal, "node": node_name, "boost": boost})

    best_node = max(scores, key=scores.get)
    trace.append({"decision": best_node, "scores": scores})
    return best_node, trace


def _extract_signals(state: AgentState, plan: list[str], idx: int) -> dict[str, bool]:
    """يستخلص إشارات قرار واضحة من حالة الوكيل."""
    if not plan:
        return {"missing_plan": True}
    if idx >= len(plan):
        return {"plan_exhausted": True}

    next_step = plan[idx]
    last_message = _safe_last_message(state)
    has_search_results = bool(state.get("search_results"))
    needs_reasoning = _detect_reasoning_need(last_message)

    return {
        "step_search": next_step == "search",
        "step_reason": next_step == "reason",
        "step_explain": next_step == "explain",
        "step_analyze": next_step == "analyze",
        "has_search_results": has_search_results,
        "needs_reasoning": needs_reasoning,
    }


def _safe_last_message(state: AgentState) -> str:
    """يعيد آخر رسالة نصية بشكل آمن للاستخدام في الإشارات."""
    messages = state.get("messages", [])
    if not messages:
        return ""
    return str(messages[-1].content)


def _detect_reasoning_need(message: str) -> bool:
    """يتحقق من مؤشرات الحاجة للاستدلال العميق."""
    lowered = message.lower()
    tokens = ["برهن", "اثبت", "حل", "proof", "derive", "compute", "احسب"]
    return any(token in lowered for token in tokens)
