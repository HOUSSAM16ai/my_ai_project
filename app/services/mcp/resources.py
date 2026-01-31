"""
موارد MCP - بيانات هيكلية للمعرفة.
===================================

يوفر موارد:
- بنية المشروع
- مخطط قاعدة البيانات
- معلومات البيئة
- الخدمات المصغرة
"""

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.overmind.knowledge_structure import (
    build_project_structure,
    build_microservices_summary,
)

logger = get_logger(__name__)


class MCPResource:
    """
    تمثيل مورد MCP.
    
    Attributes:
        uri: معرف المورد الفريد
        name: اسم المورد
        description: وصف المورد
        mime_type: نوع المحتوى
    """
    
    def __init__(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str = "application/json",
    ) -> None:
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type
    
    def to_dict(self) -> dict[str, str]:
        """تحويل لقاموس."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


class MCPResourceProvider:
    """
    مزود موارد MCP.
    
    يدير الموارد المتاحة:
    - project://structure - بنية المشروع
    - project://database - مخطط قاعدة البيانات
    - project://environment - معلومات البيئة
    - project://microservices - الخدمات المصغرة
    - project://technologies - التقنيات المستخدمة
    """
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.resources: dict[str, MCPResource] = {}
        self._cache: dict[str, dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """تهيئة الموارد."""
        
        # مورد: بنية المشروع
        self.resources["project://structure"] = MCPResource(
            uri="project://structure",
            name="بنية المشروع",
            description="معلومات شاملة عن بنية المشروع: الملفات، المجلدات، الدوال، الكلاسات",
        )
        
        # مورد: قاعدة البيانات
        self.resources["project://database"] = MCPResource(
            uri="project://database",
            name="مخطط قاعدة البيانات",
            description="الجداول، الأعمدة، العلاقات، الفهارس",
        )
        
        # مورد: البيئة
        self.resources["project://environment"] = MCPResource(
            uri="project://environment",
            name="معلومات البيئة",
            description="الإعدادات، المتغيرات البيئية (بدون الأسرار)",
        )
        
        # مورد: الخدمات المصغرة
        self.resources["project://microservices"] = MCPResource(
            uri="project://microservices",
            name="الخدمات المصغرة",
            description="معلومات عن الخدمات المصغرة في المشروع",
        )
        
        # مورد: التقنيات
        self.resources["project://technologies"] = MCPResource(
            uri="project://technologies",
            name="التقنيات المستخدمة",
            description="LangGraph, LlamaIndex, DSPy, Reranker, Kagent وغيرها",
        )
        
        # مورد: الإحصائيات السريعة
        self.resources["project://stats"] = MCPResource(
            uri="project://stats",
            name="إحصائيات سريعة",
            description="ملخص سريع لإحصائيات المشروع",
        )
        
        logger.info(f"✅ تم تهيئة {len(self.resources)} مورد MCP")
    
    async def get_resource(self, uri: str) -> dict[str, Any]:
        """
        الحصول على محتوى مورد.
        
        Args:
            uri: معرف المورد
            
        Returns:
            dict: محتوى المورد
        """
        if uri not in self.resources:
            return {
                "error": f"المورد '{uri}' غير موجود",
                "available_resources": list(self.resources.keys()),
            }
        
        # التحقق من الـ cache
        if uri in self._cache:
            return self._cache[uri]
        
        # جلب البيانات
        content = await self._fetch_resource_content(uri)
        
        # تخزين في الـ cache
        self._cache[uri] = content
        
        return content
    
    async def _fetch_resource_content(self, uri: str) -> dict[str, Any]:
        """جلب محتوى المورد."""
        
        if uri == "project://structure":
            return build_project_structure(self.project_root)
        
        elif uri == "project://microservices":
            return build_microservices_summary(self.project_root)
        
        elif uri == "project://database":
            try:
                from app.services.overmind.knowledge import ProjectKnowledge
                pk = ProjectKnowledge()
                return await pk.get_database_info()
            except Exception as e:
                return {"error": str(e), "message": "تعذر الاتصال بقاعدة البيانات"}
        
        elif uri == "project://environment":
            try:
                from app.services.overmind.knowledge import ProjectKnowledge
                pk = ProjectKnowledge()
                return pk.get_environment_info()
            except Exception as e:
                return {"error": str(e)}
        
        elif uri == "project://technologies":
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
        
        elif uri == "project://stats":
            structure = build_project_structure(self.project_root)
            microservices = build_microservices_summary(self.project_root)
            
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
        
        return {"error": f"المورد '{uri}' غير معروف"}
    
    def list_resources(self) -> list[dict[str, str]]:
        """قائمة الموارد المتاحة."""
        return [r.to_dict() for r in self.resources.values()]
    
    def clear_cache(self) -> None:
        """مسح الـ cache."""
        self._cache.clear()
        logger.debug("🗑️ تم مسح cache الموارد")
