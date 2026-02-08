"""
سجل أدوات MCP - التسجيل والتنفيذ الموحد.
==========================================

يوفر مجموعة شاملة من الأدوات:
- معرفة المشروع
- تحليل الكود
- البحث في الكود
- عمليات الملفات
- قاعدة البيانات
"""

from collections.abc import Callable, Coroutine
from pathlib import Path

from app.core.logging import get_logger
from app.services.overmind.knowledge import ProjectKnowledge
from app.services.overmind.knowledge_structure import (
    build_microservices_summary,
    build_project_structure,
    get_file_details,
    search_files_by_name,
)

logger = get_logger(__name__)


# نوع الأداة
ToolHandler = Callable[..., Coroutine[object, object, dict[str, object]]]


class MCPTool:
    """
    تمثيل أداة MCP.

    Attributes:
        name: اسم الأداة
        description: وصف الأداة
        handler: الدالة المنفذة
        parameters: معاملات الأداة (JSON Schema)
    """

    def __init__(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: dict[str, object] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {"type": "object", "properties": {}}

    async def execute(self, arguments: dict[str, object]) -> dict[str, object]:
        """تنفيذ الأداة."""
        try:
            result = await self.handler(**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الأداة {self.name}: {e}")
            return {"success": False, "error": str(e)}

    def to_openai_schema(self) -> dict[str, object]:
        """تحويل لمخطط OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class MCPToolRegistry:
    """
    سجل أدوات MCP.

    يدير تسجيل وتنفيذ جميع الأدوات.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.tools: dict[str, MCPTool] = {}
        self._project_knowledge = ProjectKnowledge()

    async def register_all_tools(self) -> None:
        """تسجيل جميع الأدوات المتاحة."""

        # أداة: إحصائيات المشروع
        self.register_tool(
            MCPTool(
                name="get_project_metrics",
                description="الحصول على إحصائيات دقيقة عن المشروع: عدد الملفات، الدوال، الكلاسات، مقسمة حسب المجلدات",
                handler=self._get_project_metrics,
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        )

        # أداة: المعرفة الكاملة
        self.register_tool(
            MCPTool(
                name="get_complete_knowledge",
                description="الحصول على المعرفة الكاملة عن المشروع: البنية، قاعدة البيانات، البيئة، الخدمات المصغرة",
                handler=self._get_complete_knowledge,
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        )

        # أداة: تحليل ملف
        self.register_tool(
            MCPTool(
                name="analyze_file",
                description="تحليل ملف بايثون معين واستخراج الدوال والكلاسات والـ imports",
                handler=self._analyze_file,
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "مسار الملف (نسبي أو مطلق)",
                        }
                    },
                    "required": ["file_path"],
                },
            )
        )

        # أداة: البحث في الملفات
        self.register_tool(
            MCPTool(
                name="search_files",
                description="البحث عن ملفات بايثون بالاسم",
                handler=self._search_files,
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "نمط البحث (جزء من اسم الملف)",
                        }
                    },
                    "required": ["pattern"],
                },
            )
        )

        # أداة: البحث في الكود
        self.register_tool(
            MCPTool(
                name="search_codebase",
                description="البحث في الكود باستخدام البحث الدلالي أو النصي",
                handler=self._search_codebase,
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "نص البحث",
                        },
                        "search_type": {
                            "type": "string",
                            "enum": ["semantic", "lexical", "hybrid"],
                            "description": "نوع البحث",
                        },
                    },
                    "required": ["query"],
                },
            )
        )

        # أداة: قائمة الدوال
        self.register_tool(
            MCPTool(
                name="list_functions",
                description="قائمة جميع الدوال في ملف أو مجلد معين",
                handler=self._list_functions,
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "مسار الملف أو المجلد",
                        }
                    },
                    "required": [],
                },
            )
        )

        # أداة: معلومات التقنيات
        self.register_tool(
            MCPTool(
                name="get_technologies",
                description="قائمة التقنيات المستخدمة في المشروع: LangGraph, LlamaIndex, DSPy, Kagent, إلخ",
                handler=self._get_technologies,
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        )

        # أداة: الخدمات المصغرة
        self.register_tool(
            MCPTool(
                name="get_microservices",
                description="معلومات عن الخدمات المصغرة في المشروع",
                handler=self._get_microservices,
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        )

        logger.info(f"✅ تم تسجيل {len(self.tools)} أداة MCP")

    def register_tool(self, tool: MCPTool) -> None:
        """تسجيل أداة جديدة."""
        self.tools[tool.name] = tool
        logger.debug(f"📦 تم تسجيل الأداة: {tool.name}")

    async def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        """
        تنفيذ أداة.

        Args:
            tool_name: اسم الأداة
            arguments: معاملات الأداة

        Returns:
            dict: نتيجة التنفيذ
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"الأداة '{tool_name}' غير موجودة. الأدوات المتاحة: {list(self.tools.keys())}",
            }

        tool = self.tools[tool_name]
        return await tool.execute(arguments)

    def list_tools(self) -> list[dict[str, str]]:
        """قائمة الأدوات المتاحة."""
        return [{"name": t.name, "description": t.description} for t in self.tools.values()]

    def get_openai_schema(self) -> list[dict[str, object]]:
        """الحصول على مخطط OpenAI لجميع الأدوات."""
        return [tool.to_openai_schema() for tool in self.tools.values()]

    # ============== معالجات الأدوات ==============

    async def _get_project_metrics(self) -> dict[str, object]:
        """الحصول على إحصائيات المشروع الدقيقة."""
        structure = build_project_structure(self.project_root)

        return {
            "total_python_files": structure["python_files"],
            "total_functions": structure["total_functions"],
            "total_classes": structure["total_classes"],
            "total_lines": structure["total_lines"],
            "by_directory": {
                dir_name: {
                    "python_files": stats["python_files"],
                    "functions": stats["total_functions"],
                    "classes": stats["total_classes"],
                }
                for dir_name, stats in structure.get("by_directory", {}).items()
            },
            "main_modules": structure.get("main_modules", []),
        }

    async def _get_complete_knowledge(self) -> dict[str, object]:
        """الحصول على المعرفة الكاملة."""
        try:
            return await self._project_knowledge.get_complete_knowledge()
        except Exception as e:
            logger.error(f"خطأ في جلب المعرفة الكاملة: {e}")
            # Fallback: معلومات البنية فقط
            return {
                "structure": build_project_structure(self.project_root),
                "microservices": build_microservices_summary(self.project_root),
                "error": str(e),
            }

    async def _analyze_file(self, file_path: str) -> dict[str, object]:
        """تحليل ملف بايثون."""
        return get_file_details(self.project_root, file_path)

    async def _search_files(self, pattern: str) -> dict[str, object]:
        """البحث عن ملفات."""
        results = search_files_by_name(self.project_root, pattern)
        return {
            "pattern": pattern,
            "count": len(results),
            "files": results,
        }

    async def _search_codebase(self, query: str, search_type: str = "lexical") -> dict[str, object]:
        """البحث في الكود."""
        try:
            from app.services.agent_tools.search_tools import (
                code_search_lexical,
                code_search_semantic,
            )

            if search_type == "semantic":
                return await code_search_semantic(query=query)
            return await code_search_lexical(query=query)
        except Exception as e:
            logger.error(f"خطأ في البحث: {e}")
            # Fallback: البحث في أسماء الملفات
            return await self._search_files(query)

    async def _list_functions(self, path: str = "app") -> dict[str, object]:
        """قائمة الدوال في مسار معين."""
        from app.services.overmind.knowledge_structure import _analyze_directory

        target_path = self.project_root / path
        if not target_path.exists():
            return {"error": f"المسار غير موجود: {path}"}

        stats = _analyze_directory(target_path, self.project_root)

        all_functions = []
        for file_info in stats.get("files", []):
            for func in file_info.get("functions", []):
                func["file"] = file_info.get("relative_path", "")
                all_functions.append(func)

        return {
            "path": path,
            "total_functions": len(all_functions),
            "functions": all_functions[:100],  # أول 100 دالة
        }

    async def _get_technologies(self) -> dict[str, object]:
        """قائمة التقنيات المستخدمة."""
        return {
            "ai_frameworks": {
                "LangGraph": {
                    "status": "active",
                    "location": "app/services/overmind/langgraph/",
                    "purpose": "تنسيق الوكلاء المتعددين",
                },
                "LlamaIndex": {
                    "status": "active",
                    "location": "microservices/research_agent/src/search_engine/",
                    "purpose": "البحث الدلالي والاسترجاع",
                },
                "DSPy": {
                    "status": "active",
                    "location": "microservices/planning_agent/cognitive.py",
                    "purpose": "تحسين الاستعلامات والتفكير",
                },
                "Reranker": {
                    "status": "active",
                    "location": "microservices/research_agent/src/search_engine/reranker.py",
                    "purpose": "إعادة ترتيب نتائج البحث",
                },
                "Kagent": {
                    "status": "active",
                    "location": "app/services/kagent/",
                    "purpose": "شبكة الوكلاء والتوجيه",
                },
            },
            "backend": {
                "FastAPI": "إطار العمل الرئيسي",
                "SQLAlchemy": "ORM لقاعدة البيانات",
                "Pydantic": "التحقق من البيانات",
                "PostgreSQL": "قاعدة البيانات",
            },
            "mcp": {
                "status": "active",
                "location": "app/services/mcp/",
                "purpose": "توحيد الأدوات والموارد",
            },
        }

    async def _get_microservices(self) -> dict[str, object]:
        """معلومات الخدمات المصغرة."""
        return build_microservices_summary(self.project_root)
