"""
البروتوكولات والواجهات الأساسية (Core Protocols & Interfaces).

يحدد الفئات الأساسية المجردة والبروتوكولات للتطبيق.
يطبق مبدأ Abstraction Barriers من SICP لفصل التعريف عن التطبيق.

المبادئ (Principles):
- Harvard CS50 2025: توثيق عربي، صرامة الأنواع
- Berkeley SICP: Abstraction Barriers (الواجهات تخفي التطبيق)
- SOLID: Interface Segregation (واجهات صغيرة ومحددة)

الاستخدام (Usage):
    class MyService:
        def __init__(self, repo: RepositoryProtocol):
            self.repo = repo  # يعمل مع أي تطبيق للبروتوكول
"""
from collections.abc import AsyncGenerator
from typing import Any, Protocol, runtime_checkable

from app.models import Mission, MissionEvent, MissionEventType, MissionStatus, Task


@runtime_checkable
class BaseService(Protocol):
    """
    بروتوكول أساسي لجميع خدمات التطبيق.
    
    يحدد الواجهة الأساسية التي يجب أن تلتزم بها جميع الخدمات.
    """
    pass

@runtime_checkable
class RepositoryProtocol(Protocol):
    """
    بروتوكول أساسي للمستودعات (Repositories).
    
    يحدد الواجهة الأساسية لعمليات الوصول للبيانات (Data Access Layer).
    """
    pass

@runtime_checkable
class CollaborationContext(Protocol):
    """
    بروتوكول سياق التعاون بين الوكلاء (Collaboration Context).
    
    يوفر آلية آمنة للخيوط (thread-safe) لتخزين واسترجاع السياق المشترك
    بين الوكلاء المختلفين في النظام.
    """
    shared_memory: dict[str, Any]

    def update(self, key: str, value: Any) -> None:
        ...

    def get(self, key: str) -> Any | None:
        ...

@runtime_checkable
class AgentPlanner(Protocol):
    """
    بروتوكول وكيل التخطيط الاستراتيجي (Strategist Agent).
    """
    async def create_plan(self, objective: str, context: CollaborationContext) -> dict[str, Any]:
        ...

@runtime_checkable
class AgentArchitect(Protocol):
    """
    بروتوكول وكيل التصميم المعماري (Architect Agent).
    """
    async def design_solution(self, plan: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """
    بروتوكول وكيل التنفيذ (Operator Agent).
    """
    async def execute_tasks(self, design: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        ...

@runtime_checkable
class AgentReflector(Protocol):
    """
    بروتوكول وكيل المراجعة والتدقيق (Auditor Agent).
    """
    async def review_work(
        self,
        result: dict[str, Any],
        original_objective: str,
        context: CollaborationContext
    ) -> dict[str, Any]:
        ...

@runtime_checkable
class MissionStateManagerProtocol(Protocol):
    """
    بروتوكول مدير حالة المهمة (Mission State Manager Protocol).

    يحدد العمليات اللازمة لإدارة حالة المهمة دون الاعتماد على التطبيق المباشر.
    """
    async def get_mission(self, mission_id: int) -> Mission | None:
        """استرجاع المهمة بواسطة المعرف."""
        ...

    async def update_mission_status(
        self, mission_id: int, status: MissionStatus, note: str | None = None
    ) -> None:
        """تحديث حالة المهمة."""
        ...

    async def log_event(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ) -> None:
        """تسجيل حدث للمهمة."""
        ...
        
    async def mark_task_running(self, task_id: int) -> None:
        """تحديث حالة المهمة إلى قيد التشغيل."""
        ...

    async def mark_task_complete(self, task_id: int, result_text: str, meta: dict | None = None) -> None:
        """تحديث حالة المهمة إلى مكتملة."""
        ...

    async def mark_task_failed(self, task_id: int, error_text: str) -> None:
        """تحديث حالة المهمة إلى فاشلة."""
        ...

    async def monitor_mission_events(
        self, mission_id: int, poll_interval: float = 1.0
    ) -> AsyncGenerator[MissionEvent, None]:
        """مراقبة أحداث المهمة."""
        ...

@runtime_checkable
class TaskExecutorProtocol(Protocol):
    """
    بروتوكول منفذ المهام (Task Executor Protocol).
    """
    async def execute_task(self, task: Task) -> dict[str, Any]:
        """تنفيذ مهمة واحدة."""
        ...

@runtime_checkable
class AIClientProtocol(Protocol):
    """
    بروتوكول عميل الذكاء الاصطناعي (AI Client Protocol).
    """
    async def generate(self, prompt: str, **kwargs) -> str:
        ...

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        ...

@runtime_checkable
class HealthCheckService(Protocol):
    """بروتوكول خدمة فحص الصحة."""
    async def check_health(self) -> dict[str, Any]: ...

@runtime_checkable
class SystemService(Protocol):
    """بروتوكول خدمة النظام."""
    async def get_system_info(self) -> dict[str, Any]: ...
