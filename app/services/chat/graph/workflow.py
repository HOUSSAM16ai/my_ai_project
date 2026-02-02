"""
بناء وتكوين سير العمل للوكلاء المتعددين (Multi-Agent Workflow).
---------------------------------------------------------------
يتولى هذا الملف مسؤولية تجميع العقد (Nodes) والحواف (Edges) لتشكيل الرسم البياني التنفيذي
(Execution Graph) باستخدام مكتبة LangGraph. يتم فيه تطبيق مبادئ
توزيع المسؤوليات (Separation of Concerns) وحقن التبعيات (Dependency Injection).
"""

from langgraph.graph import END, StateGraph

from app.core.ai_gateway import AIClient
from app.core.di import get_kagent_mesh
from app.services.chat.graph.nodes.planner import planner_node
from app.services.chat.graph.nodes.procedural_auditor import procedural_auditor_node
from app.services.chat.graph.nodes.researcher import researcher_node
from app.services.chat.graph.nodes.reviewer import reviewer_node
from app.services.chat.graph.nodes.super_reasoner import super_reasoner_node
from app.services.chat.graph.nodes.supervisor import supervisor_node
from app.services.chat.graph.nodes.writer import writer_node
from app.services.chat.graph.state import AgentState
from app.services.chat.tools import ToolRegistry


def configure_local_mesh() -> None:
    """
    تقوم بتهيئة شبكة الوكلاء المركزية (Kagent Mesh) وتسجيل الخدمات الدقيقة المحلية.

    تعمل هذه الدالة كنقطة تجميع (Composition Root) لربط تطبيقات الخدمات الدقيقة
    (Microservices) مع المحول المحلي (LocalAgentAdapter)، مما يسمح للوكلاء بالتواصل
    داخل نفس العملية (In-Process) أثناء التطوير أو النشر الأحادي.

    الآثار الجانبية:
        - تقوم باستيراد تطبيقات FastAPI من microservices/*.
        - تقوم بتسجيل الخدمات في الـ Singleton الخاص بـ KagentMesh.
    """
    # Import Microservice Apps for Local Adapter Registration
    from microservices.planning_agent.main import app as planning_app
    from microservices.reasoning_agent.main import app as reasoning_app
    from microservices.research_agent.main import app as research_app

    # Initialize Kagent Mesh and Register Services
    kagent = get_kagent_mesh()

    # Register Agents as Services (The Mesh will wrap them in LocalAgentAdapter)
    kagent.register_service(
        "reasoning_agent", reasoning_app, capabilities=["reason", "solve_deeply"]
    )
    # Alias 'reasoning_engine' to 'reasoning_agent' logic if needed, or update callers
    kagent.register_service("reasoning_engine", reasoning_app)

    kagent.register_service("research_agent", research_app, capabilities=["search", "retrieve"])
    kagent.register_service("planning_agent", planning_app, capabilities=["generate_plan"])


def create_multi_agent_graph(ai_client: AIClient, tools: ToolRegistry) -> object:
    """
    تقوم ببناء وتجميع الرسم البياني للحالة (StateGraph) الذي يدير تفاعل الوكلاء.

    تطبق هذه الدالة نمط "المشرف-العمال" (Supervisor-Worker Topology)، حيث يتحكم
    المشرف (Supervisor) في تدفق العمل ويوجه الطلبات إلى العمال المتخصصين (Planner,
    Researcher, Writer, etc.) بناءً على الحالة الحالية.

    المعاملات:
        ai_client (AIClient): عميل الذكاء الاصطناعي المستخدم للتواصل مع نماذج اللغة (LLMs).
        tools (ToolRegistry): سجل الأدوات المتاحة (غير مستخدم حاليًا بشكل مباشر في بناء الرسم،
                              ولكنه قد يمرر للوكلاء مستقبلًا).

    الإرجاع:
        object: كائن (CompiledGraph) جاهز للتنفيذ، يمثل منطق التطبيق الكامل.
    """
    configure_local_mesh()
    kagent = get_kagent_mesh()

    workflow = StateGraph(AgentState)

    def _wrap_node(node_func, dependency):
        """
        دالة مساعدة لتغليف عقد الوكلاء وحقن التبعيات اللازمة (Dependency Injection).

        تضمن هذه الدالة التزام الكود بمبدأ DRY (Don't Repeat Yourself) عبر تجريد
        منطق استدعاء العقد غير المتزامنة وتمرير العملاء (kagent أو ai_client).
        """

        async def wrapped(state):
            return await node_func(state, dependency)

        return wrapped

    # 1. Add Nodes
    workflow.add_node("planner", _wrap_node(planner_node, kagent))
    workflow.add_node("researcher", _wrap_node(researcher_node, kagent))
    workflow.add_node("super_reasoner", _wrap_node(super_reasoner_node, kagent))

    workflow.add_node("writer", _wrap_node(writer_node, ai_client))
    workflow.add_node("reviewer", _wrap_node(reviewer_node, ai_client))
    workflow.add_node("procedural_auditor", _wrap_node(procedural_auditor_node, ai_client))
    workflow.add_node("supervisor", _wrap_node(supervisor_node, ai_client))

    # 2. Add Edges
    workflow.set_entry_point("supervisor")

    # Conditional Edges from Supervisor
    # The Supervisor LLM decides exactly which node to go to next.
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer",
            "super_reasoner": "super_reasoner",
            "procedural_auditor": "procedural_auditor",
            "reviewer": "reviewer",
            "FINISH": END,
        },
    )

    # Direct Edges: All workers report back to Supervisor
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("super_reasoner", "supervisor")
    workflow.add_edge("procedural_auditor", "supervisor")
    workflow.add_edge("writer", "supervisor")
    workflow.add_edge("reviewer", "supervisor")

    return workflow.compile()
