"""
Core Protocols & Interfaces - عقود النظام الأساسية
Defines abstract base classes and protocols for the application, enforcing strict boundaries.
CS50 2025 Standard: Type-safe, documented in Arabic, and SOLID-compliant.
"""
from typing import Any, Protocol, runtime_checkable
from collections.abc import Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

__all__ = [
    "BaseService",
    "RepositoryProtocol",
    "AgentTool",
    "ToolRegistryProtocol",
    "AgentMemory",
    "AgentPlanner",
    "AgentExecutor",
    "AgentReflector",
    "AgentArchitect",
    "CollaborationContext",
    "InterAgentMessage",
    "MessagePriority",
]

@dataclass
class MessagePriority:
    """أولويات الرسائل بين الوكلاء."""
    LOW: int = 0
    NORMAL: int = 1
    HIGH: int = 2
    CRITICAL: int = 3

@dataclass
class InterAgentMessage:
    """
    رسالة متبادلة بين الوكلاء.
    Represents a structured message passed between agents in the council.
    """
    sender: str
    recipient: str
    content: dict[str, Any]
    message_type: str  # e.g., "PROPOSAL", "CRITIQUE", "COMMAND", "INFO"
    priority: int = MessagePriority.NORMAL
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CollaborationContext:
    """
    سياق التعاون المشترك.
    Shared state accessible during a multi-agent session.
    """
    mission_id: int
    objective: str
    shared_memory: dict[str, Any] = field(default_factory=dict)
    message_history: list[InterAgentMessage] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)  # Files, Code snippets, etc.

    def add_message(self, msg: InterAgentMessage) -> None:
        self.message_history.append(msg)

# ======================================================================================
# Service Protocols
# ======================================================================================

@runtime_checkable
class BaseService(Protocol):
    """
    البروتوكول الأساسي لجميع الخدمات.
    Base protocol for all application services.
    """
    pass

@runtime_checkable
class RepositoryProtocol(Protocol):
    """
    بروتوكول المستودعات (Repositories).
    """
    pass

# ======================================================================================
# AI Agent Protocols (SOLID: ISP & DIP)
# ======================================================================================

@runtime_checkable
class AgentTool(Protocol):
    """
    بروتوكول الأداة المستقلة.
    Protocol for an autonomous agent tool. Each tool must have a single responsibility (SRP).
    """
    @property
    def name(self) -> str:
        """اسم الأداة الفريد."""
        ...

    @property
    def description(self) -> str:
        """وصف وظيفة الأداة."""
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """مخطط المعاملات (JSON Schema)."""
        ...

    async def execute(self, **kwargs) -> Any:
        """
        تنفيذ منطق الأداة.
        Executes the tool logic.
        """
        ...

@runtime_checkable
class ToolRegistryProtocol(Protocol):
    """
    بروتوكول سجل الأدوات (OCP).
    Protocol for managing tools. Allows adding new tools without modifying the consumer.
    """
    def register(self, tool: AgentTool) -> None:
        """تسجيل أداة جديدة."""
        ...

    def get(self, name: str) -> AgentTool | None:
        """جلب أداة بالاسم."""
        ...

    def list_tools(self) -> list[AgentTool]:
        """سرد جميع الأدوات المتاحة."""
        ...

@runtime_checkable
class AgentMemory(Protocol):
    """
    بروتوكول ذاكرة الوكيل.
    Abstracts persistence for agents.
    """
    async def store(self, key: str, value: Any) -> None:
        ...

    async def retrieve(self, key: str) -> Any:
        ...

# ======================================================================================
# The Council of Agents Protocols (مجلس الحكماء)
# ======================================================================================

@runtime_checkable
class AgentPlanner(Protocol):
    """
    بروتوكول المخطط الاستراتيجي (Strategist).
    Responsible for breaking down objectives into plans.
    """
    @property
    def name(self) -> str:
        ...

    async def create_plan(self, objective: str, context: CollaborationContext | None = None) -> dict[str, Any]:
        """
        إنشاء خطة تنفيذ شاملة بناءً على الهدف.
        Creates a comprehensive execution plan based on the objective.
        """
        ...

@runtime_checkable
class AgentArchitect(Protocol):
    """
    بروتوكول المهندس المعماري (Architect).
    Responsible for designing the structural solution (Files, Classes, DB Schema).
    """
    @property
    def name(self) -> str:
        ...

    async def design_solution(self, plan: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """
        تصميم الهيكل البرمجي أو النظامي بناءً على الخطة المعتمدة.
        Designs the technical structure (blueprints) based on the plan.
        """
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """
    بروتوكول المنفذ التشغيلي (Operator).
    Responsible for executing atomic tasks using tools.
    """
    @property
    def name(self) -> str:
        ...

    async def execute_task(self, task: Any, context: CollaborationContext | None = None) -> dict[str, Any]:
        """
        تنفيذ مهمة محددة باستخدام الأدوات المتاحة.
        Executes a specific task using available tools.
        """
        ...

@runtime_checkable
class AgentReflector(Protocol):
    """
    بروتوكول الناقد والمدقق (Auditor/Critic).
    Responsible for reviewing plans, designs, and execution results for accuracy and safety.
    """
    @property
    def name(self) -> str:
        ...

    async def critique_plan(self, plan: dict[str, Any], objective: str) -> dict[str, Any]:
        """
        نقد الخطة المقترحة واكتشاف الثغرات.
        Reviews a plan for potential flaws or optimizations.
        """
        ...

    async def verify_execution(self, task: Any, result: dict[str, Any]) -> dict[str, Any]:
        """
        التحقق من صحة التنفيذ ومطابقته للتوقعات.
        Verifies if the execution result matches the task expectations.
        """
        ...
