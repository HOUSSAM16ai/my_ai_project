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
from typing import Any, Protocol, runtime_checkable


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
    
    الاستخدام (Usage):
        context.update("plan", strategic_plan)
        plan = context.get("plan")
    """
    shared_memory: dict[str, Any]

    def update(self, key: str, value: Any) -> None:
        """
        تحديث قيمة في الذاكرة المشتركة.
        
        Args:
            key: مفتاح القيمة
            value: القيمة المراد تخزينها
        """
        ...

    def get(self, key: str) -> Any | None:
        """
        استرجاع قيمة من الذاكرة المشتركة.
        
        Args:
            key: مفتاح القيمة
            
        Returns:
            القيمة المخزنة أو None إذا لم تكن موجودة
        """
        ...

@runtime_checkable
class AgentPlanner(Protocol):
    """
    بروتوكول وكيل التخطيط الاستراتيجي (Strategist Agent).
    
    مسؤول عن إنشاء الخطط الاستراتيجية بناءً على الأهداف المحددة.
    """
    async def create_plan(self, objective: str, context: CollaborationContext) -> dict[str, Any]:
        """
        إنشاء خطة استراتيجية بناءً على الهدف.
        
        Args:
            objective: الهدف المراد تحقيقه
            context: سياق التعاون المشترك
            
        Returns:
            الخطة الاستراتيجية
        """
        ...

@runtime_checkable
class AgentArchitect(Protocol):
    """
    بروتوكول وكيل التصميم المعماري (Architect Agent).
    
    مسؤول عن إنشاء التصاميم التقنية والمواصفات بناءً على الخطة.
    """
    async def design_solution(self, plan: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """
        إنشاء تصميم تقني بناءً على الخطة.
        
        Args:
            plan: الخطة الاستراتيجية
            context: سياق التعاون المشترك
            
        Returns:
            التصميم التقني
        """
        ...

@runtime_checkable
class AgentExecutor(Protocol):
    """
    بروتوكول وكيل التنفيذ (Operator Agent).
    
    مسؤول عن تنفيذ المهام المحددة في التصميم.
    """
    async def execute_tasks(self, design: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """
        تنفيذ المهام المحددة في التصميم.
        
        Args:
            design: التصميم التقني
            context: سياق التعاون المشترك
            
        Returns:
            نتيجة التنفيذ
        """
        ...

@runtime_checkable
class AgentReflector(Protocol):
    """
    بروتوكول وكيل المراجعة والتدقيق (Auditor Agent).
    
    مسؤول عن مراجعة نتائج التنفيذ ومقارنتها بالأهداف الأصلية.
    """
    async def review_work(
        self,
        result: dict[str, Any],
        original_objective: str,
        context: CollaborationContext
    ) -> dict[str, Any]:
        """
        مراجعة نتيجة العمل مقابل الهدف الأصلي.
        
        Args:
            result: نتيجة التنفيذ
            original_objective: الهدف الأصلي
            context: سياق التعاون المشترك
            
        Returns:
            تقرير المراجعة
        """
        ...
