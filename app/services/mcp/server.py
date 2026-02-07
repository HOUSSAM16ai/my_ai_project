"""
MCP Server الرئيسي - خادم البروتوكول الموحد.
==============================================

يوفر واجهة موحدة لـ:
- الأدوات (Tools): وظائف قابلة للاستدعاء
- الموارد (Resources): بيانات هيكلية
- المعرفة (Knowledge): معلومات المشروع

التكامل:
- LangGraph للتنسيق
- Kagent للتنفيذ
- LlamaIndex للاسترجاع
"""

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.services.mcp.resources import MCPResourceProvider
from app.services.mcp.tools import MCPToolRegistry

logger = get_logger(__name__)


class MCPServer:
    """
    خادم MCP الخارق.

    يوفر:
    - واجهة موحدة لكل الأدوات
    - تكامل مع LangGraph
    - دعم Streaming
    - أمان متقدم
    - معرفة كاملة عن المشروع

    الاستخدام:
        >>> mcp = MCPServer()
        >>> await mcp.initialize()
        >>> result = await mcp.call_tool("get_project_metrics")
        >>> knowledge = await mcp.get_complete_project_knowledge()
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """
        تهيئة خادم MCP.

        Args:
            project_root: مسار جذر المشروع (اختياري، يُستخدم CWD إذا لم يُحدد)
        """
        self.project_root = project_root or Path.cwd()
        self.tool_registry = MCPToolRegistry(self.project_root)
        self.resource_provider = MCPResourceProvider(self.project_root)
        self._initialized = False

        logger.info(f"🚀 MCP Server تم إنشاؤه في: {self.project_root}")

    async def initialize(self) -> None:
        """
        تهيئة خادم MCP وتسجيل جميع الأدوات والموارد.
        """
        if self._initialized:
            return

        logger.info("⚡ جاري تهيئة MCP Server...")

        # تسجيل الأدوات
        await self.tool_registry.register_all_tools()

        # تهيئة الموارد
        await self.resource_provider.initialize()

        self._initialized = True
        logger.info(
            f"✅ MCP Server جاهز: "
            f"{len(self.tool_registry.tools)} أداة، "
            f"{len(self.resource_provider.resources)} مورد"
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        استدعاء أداة MCP.

        Args:
            tool_name: اسم الأداة
            arguments: معاملات الأداة
            context: سياق الاستدعاء (للأمان والتحقق)

        Returns:
            dict: نتيجة الأداة
        """
        if not self._initialized:
            await self.initialize()

        # التحقق من الصلاحيات
        if not self._validate_access("call_tool", tool_name, context):
            return {
                "error": "Access Denied",
                "message": f"ليس لديك صلاحية لاستدعاء الأداة: {tool_name}",
            }

        return await self.tool_registry.execute_tool(tool_name, arguments or {})

    async def get_resource(
        self,
        resource_uri: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        الحصول على مورد MCP.

        Args:
            resource_uri: معرف المورد
            context: سياق الاستدعاء (للأمان والتحقق)

        Returns:
            dict: محتوى المورد
        """
        if not self._initialized:
            await self.initialize()

        # التحقق من الصلاحيات
        if not self._validate_access("get_resource", resource_uri, context):
            return {
                "error": "Access Denied",
                "message": f"ليس لديك صلاحية للوصول للمورد: {resource_uri}",
            }

        return await self.resource_provider.get_resource(resource_uri)

    def _validate_access(
        self,
        action: str,
        item_name: str,
        context: dict[str, Any] | None,
    ) -> bool:
        """
        التحقق من صلاحية الوصول.

        Args:
            action: نوع الإجراء (call_tool, get_resource)
            item_name: اسم العنصر
            context: سياق الاستدعاء

        Returns:
            bool: هل الوصول مسموح
        """
        # قائمة الأدوات الحساسة التي تتطلب صلاحيات إدارية
        SENSITIVE_TOOLS = {
            "execute_command",
            "write_file",
            "delete_file",
            "db_query",
            "shutdown",
        }

        # قائمة الموارد الحساسة
        SENSITIVE_RESOURCES = {
            "project://database",
            "project://environment",  # قد تحتوي على مفاتيح API
        }

        # السياق الافتراضي (للاستدعاءات الداخلية)
        if context is None:
            # يمكن اعتبار الاستدعاءات الداخلية آمنة، أو تطبيق سياسة صارمة
            # هنا سنسمح بالأدوات غير الحساسة فقط بدون سياق صريح
            if action == "call_tool" and item_name in SENSITIVE_TOOLS:
                logger.warning(f"⚠️ محاولة وصول لأداة حساسة بدون سياق: {item_name}")
                return False
            if action == "get_resource" and item_name in SENSITIVE_RESOURCES:
                logger.warning(f"⚠️ محاولة وصول لمورد حساس بدون سياق: {item_name}")
                return False
            return True

        # التحقق من الدور (Role-Based Access Control)
        role = context.get("role", "guest")

        if role == "admin":
            return True

        # المستخدم العادي لا يمكنه استخدام الأدوات الحساسة
        if action == "call_tool" and item_name in SENSITIVE_TOOLS:
            return False

        # المستخدم العادي لا يمكنه الوصول للموارد الحساسة
        if action == "get_resource" and item_name in SENSITIVE_RESOURCES:
            return False

        return True

    async def get_project_metrics(self) -> dict[str, Any]:
        """
        الحصول على إحصائيات المشروع الدقيقة.

        Returns:
            dict: إحصائيات شاملة عن المشروع
        """
        return await self.call_tool("get_project_metrics")

    async def get_complete_project_knowledge(self) -> dict[str, Any]:
        """
        الحصول على المعرفة الكاملة عن المشروع.

        يشمل:
        - بنية المشروع (كل الملفات)
        - قاعدة البيانات
        - البيئة والإعدادات
        - الخدمات المصغرة
        - التقنيات المستخدمة

        Returns:
            dict: المعرفة الكاملة
        """
        return await self.call_tool("get_complete_knowledge")

    async def analyze_file(self, file_path: str) -> dict[str, Any]:
        """
        تحليل ملف بايثون معين.

        Args:
            file_path: مسار الملف (نسبي أو مطلق)

        Returns:
            dict: تحليل تفصيلي للملف
        """
        return await self.call_tool("analyze_file", {"file_path": file_path})

    async def search_codebase(self, query: str, search_type: str = "semantic") -> dict[str, Any]:
        """
        البحث في الكود.

        Args:
            query: نص البحث
            search_type: نوع البحث (semantic, lexical, hybrid)

        Returns:
            dict: نتائج البحث
        """
        return await self.call_tool("search_codebase", {"query": query, "search_type": search_type})

    def list_tools(self) -> list[dict[str, str]]:
        """
        قائمة جميع الأدوات المتاحة.

        Returns:
            list: قائمة الأدوات مع وصفها
        """
        return self.tool_registry.list_tools()

    def list_resources(self) -> list[dict[str, str]]:
        """
        قائمة جميع الموارد المتاحة.

        Returns:
            list: قائمة الموارد مع وصفها
        """
        return self.resource_provider.list_resources()

    async def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """
        الحصول على مخطط الأدوات بتنسيق OpenAI.

        Returns:
            list: مخطط الأدوات للـ LLM
        """
        if not self._initialized:
            await self.initialize()

        return self.tool_registry.get_openai_schema()

    async def shutdown(self) -> None:
        """
        إيقاف خادم MCP.
        """
        logger.info("🛑 جاري إيقاف MCP Server...")
        self._initialized = False
        logger.info("✅ MCP Server توقف")


# Singleton instance
_mcp_server: MCPServer | None = None


def get_mcp_server(project_root: Path | None = None) -> MCPServer:
    """
    الحصول على نسخة MCPServer (Singleton).

    Args:
        project_root: مسار جذر المشروع (اختياري)

    Returns:
        MCPServer: خادم MCP
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer(project_root)
    return _mcp_server
