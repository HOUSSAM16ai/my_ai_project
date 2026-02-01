"""
نظام MCP Server الخارق لمشروع CogniForge.
===========================================

يوحد كل التقنيات المتقدمة في المشروع:
- LangGraph: تنسيق الوكلاء المتعددين
- LlamaIndex: البحث الدلالي والاسترجاع
- DSPy: تحسين الاستعلامات
- Reranker: إعادة ترتيب النتائج
- Kagent: شبكة الوكلاء

Model Context Protocol (MCP) يوفر:
- أدوات موحدة للوصول للمعرفة
- موارد للبيانات الهيكلية
- تكامل سلس مع LLMs
"""

from app.services.mcp.integrations import MCPIntegrations
from app.services.mcp.resources import MCPResourceProvider
from app.services.mcp.server import MCPServer
from app.services.mcp.tools import MCPToolRegistry

__all__ = [
    "MCPIntegrations",
    "MCPResourceProvider",
    "MCPServer",
    "MCPToolRegistry",
]
