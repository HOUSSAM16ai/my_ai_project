from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.protocols import AgentArchitect, AgentExecutor, AgentPlanner, AgentReflector
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.services.overmind.langgraph.context_enricher import ContextEnricher
from app.services.overmind.langgraph.loop_policy import LoopPolicy, should_continue_loop

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
    iteration: int
    max_iterations: int
    plan_hashes: list[str]
    loop_detected: bool


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
        loop_policy: LoopPolicy | None = None,
    ) -> None:
        self.strategist = strategist
        self.architect = architect
        self.operator = operator
        self.auditor = auditor
        self.loop_policy = loop_policy or LoopPolicy()
        self.context_enricher = ContextEnricher()
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
            "iteration": 0,
            "max_iterations": self._resolve_max_iterations(context),
            "plan_hashes": [],
            "loop_detected": False,
        }

        final_state = await self._compiled_graph.ainvoke(initial_state)
        return LangGraphRunResult(run_id=run_id, state=final_state)

    def _build_graph(self):
        """
        بناء مخطط LangGraph مركّب للوكلاء.
        """
        graph: StateGraph[LangGraphState] = StateGraph(LangGraphState)
        graph.add_node("contextualizer", self._contextualizer_node)
        graph.add_node("strategist", self._strategist_node)
        graph.add_node("architect", self._architect_node)
        graph.add_node("operator", self._operator_node)
        graph.add_node("auditor", self._auditor_node)
        graph.add_node("loop_controller", self._loop_controller_node)

        graph.set_entry_point("contextualizer")
        graph.add_edge("contextualizer", "strategist")
        graph.add_edge("strategist", "architect")
        graph.add_edge("architect", "operator")
        graph.add_edge("operator", "auditor")
        graph.add_conditional_edges(
            "auditor",
            self._route_after_audit,
            {"loop": "loop_controller", "end": END},
        )
        graph.add_edge("loop_controller", "strategist")

        return graph.compile()

    def _build_context(self, state: LangGraphState) -> InMemoryCollaborationContext:
        """
        إنشاء سياق تعاون متوافق مع بروتوكولات الوكلاء.
        """
        return InMemoryCollaborationContext(state.get("shared_memory", {}))

    def _resolve_max_iterations(self, context: dict[str, object]) -> int:
        """
        استخراج الحد الأعلى للتكرار من السياق مع حماية الحدود.
        """
        candidate = context.get("max_iterations")
        try:
            max_iterations = (
                int(candidate) if candidate is not None else self.loop_policy.max_iterations
            )
        except (TypeError, ValueError):
            max_iterations = self.loop_policy.max_iterations
        return max(1, min(max_iterations, 5))

    def _route_after_audit(self, state: LangGraphState) -> str:
        """
        توجيه التدفق بعد التدقيق وفق سياسة الحلقات.
        """
        if state.get("loop_detected"):
            return "end"

        max_iterations = state.get("max_iterations", self.loop_policy.max_iterations)
        if state.get("iteration", 0) >= max_iterations:
            return "end"

        effective_policy = LoopPolicy(
            max_iterations=max_iterations,
            approval_score=self.loop_policy.approval_score,
        )
        continue_loop = should_continue_loop(
            audit=state.get("audit"),
            iteration=state.get("iteration", 0),
            policy=effective_policy,
        )
        return "loop" if continue_loop else "end"

    def _append_timeline(
        self, state: LangGraphState, agent: str, payload: dict[str, object]
    ) -> list[dict[str, object]]:
        """
        إنشاء سجل زمني جديد مع إضافة حدث الوكيل.
        """
        return [*state.get("timeline", []), {"agent": agent, "payload": payload}]

    async def _contextualizer_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة إثراء السياق بإسناد DSPy و LlamaIndex قبل التخطيط.
        """
        enrichment = await self.context_enricher.enrich(state["objective"], state["context"])
        shared_memory = {
            **state.get("shared_memory", {}),
            "refined_objective": enrichment.refined_objective,
            "metadata_filters": enrichment.metadata,
            "knowledge_snippets": enrichment.snippets,
        }
        return {
            "shared_memory": shared_memory,
            "timeline": self._append_timeline(
                state,
                "contextualizer",
                {
                    "status": "enriched",
                    "refined_objective": enrichment.refined_objective,
                    "snippets_count": len(enrichment.snippets),
                },
            ),
        }

    async def _strategist_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة الاستراتيجي في LangGraph.
        """
        context = self._build_context(state)
        objective = context.shared_memory.get("refined_objective", state["objective"])
        plan = await self.strategist.create_plan(str(objective), context)
        context.update("last_plan", plan)
        plan_hashes = list(state.get("plan_hashes", []))
        try:
            if hasattr(self.auditor, "detect_loop"):
                self.auditor.detect_loop(plan_hashes, plan)
            if hasattr(self.auditor, "compute_plan_hash"):
                plan_hashes.append(self.auditor.compute_plan_hash(plan))
        except Exception as exc:
            context.update("loop_error", str(exc))
            return {
                "plan": plan,
                "shared_memory": context.shared_memory,
                "plan_hashes": plan_hashes,
                "loop_detected": True,
                "timeline": self._append_timeline(
                    state, "strategist", {"status": "loop_detected", "error": str(exc)}
                ),
            }
        return {
            "plan": plan,
            "shared_memory": context.shared_memory,
            "plan_hashes": plan_hashes,
            "timeline": self._append_timeline(state, "strategist", {"status": "planned"}),
        }

    async def _architect_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة المعماري في LangGraph.
        """
        if state.get("loop_detected"):
            return {
                "timeline": self._append_timeline(
                    state, "architect", {"status": "skipped_due_to_loop"}
                )
            }
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
        if state.get("loop_detected"):
            return {
                "timeline": self._append_timeline(
                    state, "operator", {"status": "skipped_due_to_loop"}
                )
            }
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
        if state.get("loop_detected"):
            return {
                "audit": {
                    "approved": False,
                    "feedback": "تم إيقاف الدورة بسبب اكتشاف حلقة تكرارية مفرغة.",
                    "score": 0.0,
                },
                "timeline": self._append_timeline(state, "auditor", {"status": "loop_stopped"}),
            }
        context = self._build_context(state)
        execution = state.get("execution") or {}
        audit = await self.auditor.review_work(execution, state["objective"], context)
        context.update("last_audit", audit)
        return {
            "audit": audit,
            "shared_memory": context.shared_memory,
            "timeline": self._append_timeline(state, "auditor", {"status": "audited"}),
        }

    async def _loop_controller_node(self, state: LangGraphState) -> dict[str, object]:
        """
        عقدة ضبط الحلقة لإعادة التخطيط استناداً إلى ملاحظات التدقيق.
        """
        next_iteration = state.get("iteration", 0) + 1
        audit = state.get("audit") or {}
        feedback = ""
        if isinstance(audit, dict):
            feedback = str(audit.get("feedback") or "")
        shared_memory = {
            **state.get("shared_memory", {}),
            "audit_feedback": feedback,
            "iteration": next_iteration,
        }
        return {
            "iteration": next_iteration,
            "shared_memory": shared_memory,
            "timeline": self._append_timeline(
                state,
                "loop_controller",
                {"status": "replan", "iteration": next_iteration},
            ),
        }
