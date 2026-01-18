from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.services.overmind.domain.context import InMemoryCollaborationContext

logger = logging.getLogger(__name__)


class LangGraphState(TypedDict):
    """
    حالة LangGraph المشتركة بين الوكلاء.

    تمثل هذه البنية الواجهة الموحدة لنقل البيانات عبر العقد،
    مع الحفاظ على الحواجز التجريدية وتجنب الاعتمادات المتشابكة.
    """

    objective: str
    context: dict[str, object]
    constraints: list[str]
    priority: str
    shared_memory: dict[str, object]
    plan: dict[str, object] | None
    design: dict[str, object] | None
    execution: dict[str, object] | None
    audit: dict[str, object] | None
    timeline: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class LangGraphRunResult:
    """
    نتيجة تشغيل LangGraph بعد اكتمال دورة الوكلاء.
    """

    run_id: str
    state: LangGraphState


class LangGraphOvermindEngine:
    """
    محرك LangGraph لمنظومة الوكلاء الخارقين.

    يبني هذا المحرك مخططاً معرفياً متسلسلاً (Strategist -> Architect -> Operator -> Auditor)
    مع تمرير حالة مشتركة واضحة، مما يعزز الاتساق مع فلسفة Functional Core/Imperative Shell.
    """

    def __init__(
        self,
        *,
        strategist: AgentPlanner,
        architect: AgentArchitect,
        operator: AgentExecutor,
        auditor: AgentReflector,
    ) -> None:
        self.strategist = strategist
        self.architect = architect
        self.operator = operator
        self.auditor = auditor
        self._compiled_graph = self._build_graph()

    async def run(
        self,
        *,
        run_id: str,
        objective: str,
        context: dict[str, object],
        constraints: list[str],
        priority: str,
    ) -> LangGraphRunResult:
        """
        تشغيل دورة LangGraph كاملة مع الحفاظ على حالة مشتركة.

        Args:
            run_id: معرف التشغيل.
            objective: الهدف الرئيسي.
            context: سياق إضافي.
            constraints: قيود تشغيلية.
            priority: أولوية الطلب.

        Returns:
            LangGraphRunResult: حالة التشغيل النهائية.
        """
        initial_state: LangGraphState = {
            "objective": objective,
            "context": context,
            "constraints": constraints,
            "priority": priority,
            "shared_memory": {
                "request_context": context,
                "constraints": constraints,
                "priority": priority,
            },
            "plan": None,
            "design": None,
            "execution": None,
            "audit": None,
            "timeline": [],
        }

        final_state = await self._compiled_graph.ainvoke(initial_state)
        return LangGraphRunResult(run_id=run_id, state=final_state)

    def _build_graph(self):
        """
        بناء مخطط LangGraph مركّب للوكلاء.
        """
        graph: StateGraph[LangGraphState] = StateGraph(LangGraphState)
        graph.add_node("strategist", self._strategist_node)
        graph.add_node("architect", self._architect_node)
        graph.add_node("operator", self._operator_node)
        graph.add_node("auditor", self._auditor_node)

        graph.set_entry_point("strategist")
        graph.add_edge("strategist", "architect")
        graph.add_edge("architect", "operator")
        graph.add_edge("operator", "auditor")
        graph.add_edge("auditor", END)

        return graph.compile()

    def _build_context(self, state: LangGraphState) -> InMemoryCollaborationContext:
        """
        إنشاء سياق تعاون متوافق مع بروتوكولات الوكلاء.
        """
        return InMemoryCollaborationContext(state.get("shared_memory", {}))

    def _append_timeline(
        self, state: LangGraphState, agent: str, payload: dict[str, object]
    ) -> list[dict[str, object]]:
        """
        إنشاء سجل زمني جديد مع إضافة حدث الوكيل.
        """
        return [*state.get("timeline", []), {"agent": agent, "payload": payload}]

    async def _strategist_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة الاستراتيجي في LangGraph.
        """
        context = self._build_context(state)
        plan = await self.strategist.create_plan(state["objective"], context)
        context.update("last_plan", plan)
        return {
            "plan": plan,
            "shared_memory": context.shared_memory,
            "timeline": self._append_timeline(state, "strategist", {"status": "planned"}),
        }

    async def _architect_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة المعماري في LangGraph.
        """
        context = self._build_context(state)
        plan = state.get("plan") or {}
        design = await self.architect.design_solution(plan, context)
        context.update("last_design", design)
        return {
            "design": design,
            "shared_memory": context.shared_memory,
            "timeline": self._append_timeline(state, "architect", {"status": "designed"}),
        }

    async def _operator_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة المنفذ في LangGraph.
        """
        context = self._build_context(state)
        design = state.get("design") or {}
        execution = await self.operator.execute_tasks(design, context)
        context.update("last_execution", execution)
        return {
            "execution": execution,
            "shared_memory": context.shared_memory,
            "timeline": self._append_timeline(state, "operator", {"status": "executed"}),
        }

    async def _auditor_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة المدقق في LangGraph.
        """
        context = self._build_context(state)
        execution = state.get("execution") or {}
        audit = await self.auditor.review_work(execution, state["objective"], context)
        context.update("last_audit", audit)
        return {
            "audit": audit,
            "shared_memory": context.shared_memory,
            "timeline": self._append_timeline(state, "auditor", {"status": "audited"}),
        }
