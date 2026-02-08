"""
موارد MCP - بيانات هيكلية للمعرفة.
===================================

يوفر موارد:
- بنية المشروع
- مخطط قاعدة البيانات
- معلومات البيئة
- الخدمات المصغرة
"""

import time
from pathlib import Path

from app.core.logging import get_logger
from app.services.mcp.protocols import IResourceFetcher

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

    def __init__(
        self,
        project_root: Path,
        fetchers: list[IResourceFetcher] | None = None,
    ) -> None:
        self.project_root = project_root
        self.resources: dict[str, MCPResource] = {}
        # Cache stores (content, timestamp)
        self._cache: dict[str, tuple[dict[str, object], float]] = {}

        # تسجيل fetchers (OCP: يمكن إضافة fetchers جديدة بدون تعديل الكود)
        from app.services.mcp.protocols import get_default_fetchers

        self._fetchers: dict[str, IResourceFetcher] = {}
        for fetcher in fetchers or get_default_fetchers():
            self._fetchers[fetcher.uri] = fetcher

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

        # ============== Genius Services Resources ==============

        # مورد: خدمات التعلم التكيفي
        self.resources["genius://learning"] = MCPResource(
            uri="genius://learning",
            name="التعلم التكيفي",
            description="ملف الطالب، تكييف الصعوبة، تتبع الإتقان",
        )

        # مورد: الرسم البياني المعرفي
        self.resources["genius://knowledge"] = MCPResource(
            uri="genius://knowledge",
            name="الرسم البياني للمفاهيم",
            description="المفاهيم التعليمية، المتطلبات السابقة، مسارات التعلم",
        )

        # مورد: التحليل التنبؤي
        self.resources["genius://analytics"] = MCPResource(
            uri="genius://analytics",
            name="التحليل التنبؤي",
            description="التنبؤ بنقاط الضعف، كشف أنماط الأخطاء",
        )

        # مورد: خدمات الرؤية
        self.resources["genius://vision"] = MCPResource(
            uri="genius://vision",
            name="معالجة الوسائط المتعددة",
            description="تحليل الصور، كشف المعادلات، فهم الرسوم البيانية",
        )

        # مورد: التعلم التعاوني
        self.resources["genius://collaboration"] = MCPResource(
            uri="genius://collaboration",
            name="التعلم التعاوني",
            description="جلسات دراسة جماعية، مساحات عمل مشتركة",
        )

        logger.info(f"✅ تم تهيئة {len(self.resources)} مورد MCP")

    async def get_resource(self, uri: str, ttl: float = 300.0) -> dict[str, object]:
        """
        الحصول على محتوى مورد.

        Args:
            uri: معرف المورد
            ttl: مدة صلاحية الـ cache بالثواني (الافتراضي 5 دقائق)

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
            content, timestamp = self._cache[uri]
            if time.time() - timestamp < ttl:
                return content

        # جلب البيانات باستخدام fetcher
        content = await self._fetch_resource_content(uri)

        # تخزين في الـ cache مع الوقت الحالي
        self._cache[uri] = (content, time.time())

        return content

    async def _fetch_resource_content(self, uri: str) -> dict[str, object]:
        """جلب محتوى المورد باستخدام Fetcher المناسب (OCP)."""

        fetcher = self._fetchers.get(uri)
        if fetcher:
            return await fetcher.fetch(self.project_root)

        return {"error": f"المورد '{uri}' غير معروف"}

    def list_resources(self) -> list[dict[str, str]]:
        """قائمة الموارد المتاحة."""
        return [r.to_dict() for r in self.resources.values()]

    def clear_cache(self) -> None:
        """مسح الـ cache."""
        self._cache.clear()
        logger.debug("🗑️ تم مسح cache الموارد")

    def register_fetcher(self, fetcher: IResourceFetcher) -> None:
        """
        تسجيل fetcher جديد (OCP: التوسع بدون تعديل).

        Args:
            fetcher: fetcher يطبق IResourceFetcher
        """
        self._fetchers[fetcher.uri] = fetcher
        logger.debug(f"📦 تم تسجيل fetcher: {fetcher.uri}")
