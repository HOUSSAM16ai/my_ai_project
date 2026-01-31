"""
اختبارات شاملة لمكونات MCP Tools.
=================================

يغطي:
- MCPTool: إنشاء وتنفيذ وتحويل لمخطط OpenAI
- MCPToolRegistry: تسجيل وتنفيذ الأدوات
"""

from unittest.mock import patch

import pytest


class TestMCPTool:
    """اختبارات MCPTool."""

    def test_create_tool_with_defaults(self):
        """إنشاء أداة بالقيم الافتراضية."""
        from app.services.mcp.tools import MCPTool

        async def handler():
            return {"result": "ok"}

        tool = MCPTool(
            name="test_tool",
            description="أداة اختبار",
            handler=handler,
        )

        assert tool.name == "test_tool"
        assert tool.description == "أداة اختبار"
        assert tool.parameters == {"type": "object", "properties": {}}

    def test_create_tool_with_parameters(self):
        """إنشاء أداة مع معاملات مخصصة."""
        from app.services.mcp.tools import MCPTool

        async def handler(query: str):
            return {"query": query}

        params = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "نص البحث"}
            },
            "required": ["query"],
        }

        tool = MCPTool(
            name="search",
            description="بحث",
            handler=handler,
            parameters=params,
        )

        assert tool.parameters == params

    async def test_execute_success(self):
        """تنفيذ ناجح للأداة."""
        from app.services.mcp.tools import MCPTool

        async def handler(x: int, y: int):
            return {"sum": x + y}

        tool = MCPTool(name="add", description="جمع", handler=handler)

        result = await tool.execute({"x": 5, "y": 3})

        assert result["success"] is True
        assert result["result"]["sum"] == 8

    async def test_execute_handles_error(self):
        """التنفيذ يتعامل مع الأخطاء."""
        from app.services.mcp.tools import MCPTool

        async def handler():
            raise ValueError("خطأ اختبار")

        tool = MCPTool(name="error_tool", description="أداة خطأ", handler=handler)

        result = await tool.execute({})

        assert result["success"] is False
        assert "خطأ اختبار" in result["error"]

    def test_to_openai_schema(self):
        """تحويل لمخطط OpenAI."""
        from app.services.mcp.tools import MCPTool

        async def handler(query: str):
            return {}

        params = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

        tool = MCPTool(
            name="search",
            description="بحث في الكود",
            handler=handler,
            parameters=params,
        )

        schema = tool.to_openai_schema()

        assert schema == {
            "type": "function",
            "function": {
                "name": "search",
                "description": "بحث في الكود",
                "parameters": params,
            }
        }


class TestMCPToolRegistry:
    """اختبارات MCPToolRegistry."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """إنشاء بنية مشروع وهمية."""
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("# Main")
        return tmp_path

    @pytest.fixture
    def registry(self, project_root):
        """إنشاء registry للاختبارات."""
        from app.services.mcp.tools import MCPToolRegistry
        return MCPToolRegistry(project_root)

    def test_register_tool(self, registry):
        """تسجيل أداة جديدة."""
        from app.services.mcp.tools import MCPTool

        async def handler():
            return {"ok": True}

        tool = MCPTool(name="test", description="اختبار", handler=handler)
        registry.register_tool(tool)

        assert "test" in registry.tools
        assert registry.tools["test"] == tool

    async def test_register_all_tools(self, project_root):
        """تسجيل جميع الأدوات الافتراضية."""
        from app.services.mcp.tools import MCPToolRegistry

        with patch("app.services.mcp.tools.ProjectKnowledge"):
            registry = MCPToolRegistry(project_root)
            await registry.register_all_tools()

        assert len(registry.tools) >= 8
        assert "get_project_metrics" in registry.tools
        assert "get_complete_knowledge" in registry.tools
        assert "analyze_file" in registry.tools
        assert "search_files" in registry.tools

    async def test_execute_tool_success(self, registry):
        """تنفيذ أداة موجودة."""
        from app.services.mcp.tools import MCPTool

        async def handler(x: int):
            return {"doubled": x * 2}

        tool = MCPTool(name="double", description="مضاعفة", handler=handler)
        registry.register_tool(tool)

        result = await registry.execute_tool("double", {"x": 5})

        assert result["success"] is True
        assert result["result"]["doubled"] == 10

    async def test_execute_tool_not_found(self, registry):
        """تنفيذ أداة غير موجودة."""
        result = await registry.execute_tool("nonexistent", {})

        assert result["success"] is False
        assert "غير موجودة" in result["error"]

    def test_list_tools(self, registry):
        """قائمة الأدوات."""
        from app.services.mcp.tools import MCPTool

        async def h1():
            return {}
        async def h2():
            return {}

        registry.register_tool(MCPTool(name="tool1", description="أداة 1", handler=h1))
        registry.register_tool(MCPTool(name="tool2", description="أداة 2", handler=h2))

        tools = registry.list_tools()

        assert len(tools) == 2
        assert any(t["name"] == "tool1" for t in tools)
        assert any(t["name"] == "tool2" for t in tools)

    def test_get_openai_schema(self, registry):
        """الحصول على مخطط OpenAI."""
        from app.services.mcp.tools import MCPTool

        async def handler():
            return {}

        registry.register_tool(MCPTool(
            name="test",
            description="اختبار",
            handler=handler,
            parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        ))

        schema = registry.get_openai_schema()

        assert len(schema) == 1
        assert schema[0]["type"] == "function"
        assert schema[0]["function"]["name"] == "test"


class TestToolHandlers:
    """اختبارات معالجات الأدوات."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """إنشاء بنية مشروع للاختبارات."""
        app_dir = tmp_path / "app"
        app_dir.mkdir()

        services_dir = app_dir / "services"
        services_dir.mkdir()
        (services_dir / "test.py").write_text("""
class TestService:
    def method1(self):
        pass
    
    def method2(self):
        pass
""")

        return tmp_path

    async def test_get_project_metrics(self, project_root):
        """اختبار الحصول على إحصائيات المشروع."""
        from app.services.mcp.tools import MCPToolRegistry

        with patch("app.services.mcp.tools.build_project_structure") as mock:
            mock.return_value = {
                "python_files": 10,
                "total_functions": 25,
                "total_classes": 5,
                "total_lines": 500,
                "by_directory": {},
                "main_modules": [],
            }

            with patch("app.services.mcp.tools.ProjectKnowledge"):
                registry = MCPToolRegistry(project_root)
                await registry.register_all_tools()

            result = await registry.execute_tool("get_project_metrics", {})

        assert result["success"] is True
        assert result["result"]["total_python_files"] == 10

    async def test_search_files(self, project_root):
        """اختبار البحث عن ملفات."""
        from app.services.mcp.tools import MCPToolRegistry

        with patch("app.services.mcp.tools.search_files_by_name") as mock:
            mock.return_value = ["app/services/test.py"]

            with patch("app.services.mcp.tools.ProjectKnowledge"):
                registry = MCPToolRegistry(project_root)
                await registry.register_all_tools()

            result = await registry.execute_tool("search_files", {"pattern": "test"})

        assert result["success"] is True
        assert result["result"]["count"] == 1
        assert "test.py" in result["result"]["files"][0]

    async def test_analyze_file(self, project_root):
        """اختبار تحليل ملف."""
        from app.services.mcp.tools import MCPToolRegistry

        with patch("app.services.mcp.tools.get_file_details") as mock:
            mock.return_value = {
                "file": "test.py",
                "classes": ["TestService"],
                "functions": ["method1", "method2"],
            }

            with patch("app.services.mcp.tools.ProjectKnowledge"):
                registry = MCPToolRegistry(project_root)
                await registry.register_all_tools()

            result = await registry.execute_tool(
                "analyze_file",
                {"file_path": "app/services/test.py"}
            )

        assert result["success"] is True
        assert "TestService" in result["result"]["classes"]

    async def test_get_technologies(self, project_root):
        """اختبار الحصول على التقنيات."""
        from app.services.mcp.tools import MCPToolRegistry

        with patch("app.services.mcp.tools.ProjectKnowledge"):
            registry = MCPToolRegistry(project_root)
            await registry.register_all_tools()

        result = await registry.execute_tool("get_technologies", {})

        assert result["success"] is True
        assert "ai_frameworks" in result["result"]
        assert "LangGraph" in result["result"]["ai_frameworks"]
