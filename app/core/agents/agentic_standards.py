"""
معايير الوكالة الخارقة (Agentic Standards) بوصفها بيانات قابلة للتحقق.

يُعرّف هذا الملف قائمة معيارية قابلة للفحص البرمجي تعتمد على "البيانات ككود".
يتم استخدام هذه البيانات داخل أدوات التدقيق للتحقق من وجود الأدلة البرمجية
التي تثبت تطبيق معايير الاستقلالية، التحكم، والذاكرة.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceRule:
    """قاعدة تحقق مفردة تربط المعيار بدليل برمجي محدد."""

    kind: str
    path: str
    symbol: str
    owner: str | None = None
    description: str = ""


@dataclass(frozen=True)
class AgenticStandard:
    """يمثل معياراً واحداً مع الأدلة البرمجية المطلوبة لإثباته."""

    standard_id: str
    title: str
    description: str
    rules: tuple[EvidenceRule, ...]


AGENTIC_STANDARDS: tuple[AgenticStandard, ...] = (
    AgenticStandard(
        standard_id="circuit_breaker_control",
        title="قاطع الدائرة ونقاط التحكم",
        description="ضمان وجود قاطع دائرة مركزي واستعماله في بوابة الخدمات.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/core/resilience/circuit_breaker.py",
                symbol="CircuitBreaker",
                description="وجود تطبيق مركزي لنمط قاطع الدائرة.",
            ),
            EvidenceRule(
                kind="class",
                path="app/core/resilience/circuit_breaker.py",
                symbol="CircuitBreakerRegistry",
                description="وجود سجل موحد لإدارة قواطع الدائرة.",
            ),
            EvidenceRule(
                kind="call",
                path="app/core/gateway/mesh.py",
                symbol="CircuitBreaker",
                description="تفعيل قاطع الدائرة ضمن بوابة الخدمات.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="reflexion_loop",
        title="الانعكاس والتصحيح الذاتي",
        description="وجود حلقة انعكاس ذاتي مع عداد محاولات وتقييم نقدي.",
        rules=(
            EvidenceRule(
                kind="method",
                path="app/services/overmind/domain/cognitive.py",
                symbol="_execute_reflection_phase",
                owner="SuperBrain",
                description="مرحلة انعكاس صريحة داخل الدماغ الخارق.",
            ),
            EvidenceRule(
                kind="attribute",
                path="app/services/overmind/domain/cognitive.py",
                symbol="iteration_count",
                owner="CognitiveState",
                description="عداد محاولات مضمّن للحفاظ على ميزانية التنفيذ.",
            ),
            EvidenceRule(
                kind="attribute",
                path="app/services/overmind/domain/cognitive.py",
                symbol="max_iterations",
                owner="CognitiveState",
                description="حد أقصى لمحاولات التصحيح الذاتي.",
            ),
            EvidenceRule(
                kind="call",
                path="app/services/overmind/domain/cognitive.py",
                symbol="_execute_reflection_phase",
                description="دعوة مرحلة الانعكاس ضمن دورة الحل.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="explicit_control_flow",
        title="تدفق تحكم صريح عبر الرسم البياني",
        description="تعريف الرسوم البيانية للعقد والوكلاء كبيانات قابلة للتتبع.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/services/overmind/graph/orchestrator.py",
                symbol="DecentralizedGraphOrchestrator",
                description="مُنسّق الرسم البياني اللامركزي.",
            ),
            EvidenceRule(
                kind="class",
                path="app/services/overmind/graph/nodes.py",
                symbol="AgentNode",
                description="تعريف عقدة الوكيل ضمن الرسم البياني.",
            ),
            EvidenceRule(
                kind="class",
                path="app/services/overmind/graph/nodes.py",
                symbol="AgentMessage",
                description="تعريف الرسائل المتبادلة بين الوكلاء.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="mcp_protocol",
        title="بروتوكول سياق النموذج (MCP)",
        description="واجهة معيارية لاكتشاف الأدوات واستدعائها بشكل آمن.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/core/protocols.py",
                symbol="MCPToolDescriptor",
                description="وصف موحد للأداة المدعومة عبر MCP.",
            ),
            EvidenceRule(
                kind="class",
                path="app/core/protocols.py",
                symbol="MCPServerProtocol",
                description="بروتوكول خادم MCP للاكتشاف والاستدعاء.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="a2a_protocol",
        title="بروتوكول وكيل-إلى-وكيل (A2A)",
        description="واجهة تفويض وتسليم سياق بين الوكلاء.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/core/protocols.py",
                symbol="AgentHandoffProtocol",
                description="بروتوكول لتسليم السياق بين الوكلاء.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="graph_rag_memory",
        title="ذاكرة GraphRAG",
        description="نماذج رسم بياني معرفي لاسترجاع السياق المعقد.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/services/project_context/domain/graph_rag.py",
                symbol="GraphRAGIndex",
                description="بنية فهرس GraphRAG للذاكرة المهيكلة.",
            ),
            EvidenceRule(
                kind="function",
                path="app/services/project_context/domain/graph_rag.py",
                symbol="query_graph",
                description="دالة استعلام رسم بياني لاسترجاع المعرفة.",
            ),
        ),
    ),
    AgenticStandard(
        standard_id="long_memory_eval",
        title="تقييم الذاكرة طويلة المدى (LongMemEval)",
        description="نماذج تقييم تتبع التحديثات والاسترجاع والامتناع.",
        rules=(
            EvidenceRule(
                kind="class",
                path="app/services/project_context/domain/long_memory_eval.py",
                symbol="LongMemoryScore",
                description="نتيجة تقييم موحدة للذاكرة الطويلة.",
            ),
            EvidenceRule(
                kind="function",
                path="app/services/project_context/domain/long_memory_eval.py",
                symbol="evaluate_long_memory",
                description="دالة تقييم سلوك الذاكرة طويلة المدى.",
            ),
        ),
    ),
)


def get_agentic_standards() -> tuple[AgenticStandard, ...]:
    """يعيد قائمة المعايير الوكيلية المدعومة داخل النظام."""

    return AGENTIC_STANDARDS
