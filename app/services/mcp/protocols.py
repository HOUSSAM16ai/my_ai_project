"""
واجهات Protocol لمكونات MCP - تطبيق مبدأ Dependency Inversion.
===============================================================

يوفر واجهات مجردة لـ:
- IProjectKnowledge: معرفة المشروع
- IResourceFetcher: جلب الموارد
- IToolHandler: معالج الأدوات
"""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IProjectKnowledge(Protocol):
    """
    واجهة للحصول على معرفة المشروع.
    
    تتيح استبدال التنفيذ الحقيقي بـ mocks للاختبارات.
    """
    
    async def get_complete_knowledge(self) -> dict[str, Any]:
        """الحصول على المعرفة الكاملة عن المشروع."""
        ...
    
    async def get_database_info(self) -> dict[str, Any]:
        """الحصول على معلومات قاعدة البيانات."""
        ...
    
    def get_environment_info(self) -> dict[str, Any]:
        """الحصول على معلومات البيئة."""
        ...


@runtime_checkable
class IResourceFetcher(Protocol):
    """
    واجهة لجلب محتوى مورد معين (Strategy Pattern).
    
    كل مورد له fetcher خاص به يطبق هذه الواجهة.
    """
    
    @property
    def uri(self) -> str:
        """معرف المورد الذي يتعامل معه هذا الـ fetcher."""
        ...
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        """جلب محتوى المورد."""
        ...


@runtime_checkable
class IToolExecutor(Protocol):
    """
    واجهة لتنفيذ أداة MCP.
    """
    
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """تنفيذ الأداة بالمعاملات المحددة."""
        ...


@runtime_checkable
class IIntegrationService(Protocol):
    """
    واجهة عامة للتكاملات الخارجية.
    """
    
    def get_status(self) -> dict[str, Any]:
        """الحصول على حالة التكامل."""
        ...


# ============== Resource Fetchers الملموسة ==============


class StructureFetcher:
    """جلب بنية المشروع."""
    
    uri = "project://structure"
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        from app.services.overmind.knowledge_structure import build_project_structure
        return build_project_structure(project_root)


class MicroservicesFetcher:
    """جلب معلومات الخدمات المصغرة."""
    
    uri = "project://microservices"
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        from app.services.overmind.knowledge_structure import build_microservices_summary
        return build_microservices_summary(project_root)


class DatabaseFetcher:
    """جلب معلومات قاعدة البيانات."""
    
    uri = "project://database"
    
    def __init__(self, knowledge: IProjectKnowledge | None = None):
        self._knowledge = knowledge
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        try:
            if self._knowledge:
                return await self._knowledge.get_database_info()
            from app.services.overmind.knowledge import ProjectKnowledge
            pk = ProjectKnowledge()
            return await pk.get_database_info()
        except Exception as e:
            return {"error": str(e), "message": "تعذر الاتصال بقاعدة البيانات"}


class EnvironmentFetcher:
    """جلب معلومات البيئة."""
    
    uri = "project://environment"
    
    def __init__(self, knowledge: IProjectKnowledge | None = None):
        self._knowledge = knowledge
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        try:
            if self._knowledge:
                return self._knowledge.get_environment_info()
            from app.services.overmind.knowledge import ProjectKnowledge
            pk = ProjectKnowledge()
            return pk.get_environment_info()
        except Exception as e:
            return {"error": str(e)}


class TechnologiesFetcher:
    """جلب معلومات التقنيات المستخدمة."""
    
    uri = "project://technologies"
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        return {
            "ai_frameworks": [
                {
                    "name": "LangGraph",
                    "status": "✅ نشط",
                    "location": "app/services/overmind/langgraph/",
                    "description": "محرك الوكلاء المتعددين باستخدام الرسوم البيانية",
                },
                {
                    "name": "LlamaIndex",
                    "status": "✅ نشط",
                    "location": "microservices/research_agent/src/search_engine/",
                    "description": "البحث الدلالي واسترجاع المعلومات",
                },
                {
                    "name": "DSPy",
                    "status": "✅ نشط",
                    "location": "microservices/planning_agent/",
                    "description": "البرمجة التصريحية للـ LLMs",
                },
                {
                    "name": "Reranker",
                    "status": "✅ نشط",
                    "location": "microservices/research_agent/src/search_engine/reranker.py",
                    "description": "إعادة ترتيب نتائج البحث بنموذج BAAI/bge-reranker",
                },
                {
                    "name": "Kagent",
                    "status": "✅ نشط",
                    "location": "app/services/kagent/",
                    "description": "شبكة الوكلاء للتوجيه والتنفيذ",
                },
                {
                    "name": "MCP Server",
                    "status": "✅ نشط",
                    "location": "app/services/mcp/",
                    "description": "بروتوكول السياق الموحد للأدوات والموارد",
                },
            ],
            "backend": [
                {"name": "FastAPI", "purpose": "إطار العمل الرئيسي"},
                {"name": "SQLAlchemy", "purpose": "ORM غير متزامن"},
                {"name": "Pydantic v2", "purpose": "التحقق من البيانات"},
                {"name": "PostgreSQL", "purpose": "قاعدة البيانات"},
            ],
        }


class StatsFetcher:
    """جلب إحصائيات سريعة عن المشروع."""
    
    uri = "project://stats"
    
    async def fetch(self, project_root: Path) -> dict[str, Any]:
        from app.services.overmind.knowledge_structure import (
            build_project_structure,
            build_microservices_summary,
        )
        
        structure = build_project_structure(project_root)
        microservices = build_microservices_summary(project_root)
        
        return {
            "summary": {
                "total_python_files": structure["python_files"],
                "total_functions": structure["total_functions"],
                "total_classes": structure["total_classes"],
                "total_lines": structure["total_lines"],
                "total_microservices": microservices["total_services"],
            },
            "by_directory": structure.get("by_directory", {}),
            "microservices": microservices.get("services_names", []),
        }


# ============== Registry للـ Fetchers ==============


def get_default_fetchers() -> list[IResourceFetcher]:
    """الحصول على قائمة الـ fetchers الافتراضية."""
    return [
        StructureFetcher(),
        MicroservicesFetcher(),
        DatabaseFetcher(),
        EnvironmentFetcher(),
        TechnologiesFetcher(),
        StatsFetcher(),
    ]
