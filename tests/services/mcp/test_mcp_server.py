"""
اختبارات شاملة لـ MCP Server.
============================

يغطي:
- تهيئة وإغلاق الخادم
- استدعاء الأدوات والموارد
- Singleton pattern
- طرق الوصول المختصرة
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPServer:
    """اختبارات MCPServer."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """إنشاء بنية مشروع وهمية."""
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("# Main app")
        return tmp_path

    @pytest.fixture
    def mock_registry(self):
        """إنشاء registry وهمي."""
        registry = MagicMock()
        registry.tools = {}
        registry.register_all_tools = AsyncMock()
        registry.execute_tool = AsyncMock(return_value={"success": True, "result": {}})
        registry.list_tools = MagicMock(return_value=[])
        registry.get_openai_schema = MagicMock(return_value=[])
        return registry

    @pytest.fixture
    def mock_provider(self):
        """إنشاء provider وهمي."""
        provider = MagicMock()
        provider.resources = {}
        provider.initialize = AsyncMock()
        provider.get_resource = AsyncMock(return_value={"data": "test"})
        provider.list_resources = MagicMock(return_value=[])
        return provider

    async def test_initialize(self, project_root):
        """اختبار التهيئة."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {"tool1": None}
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {"res1": None}

            server = MCPServer(project_root)
            await server.initialize()

            assert server._initialized is True
            mock_registry.return_value.register_all_tools.assert_called_once()
            mock_provider.return_value.initialize.assert_called_once()

    async def test_initialize_only_once(self, project_root):
        """التهيئة مرة واحدة فقط."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)

            await server.initialize()
            await server.initialize()  # استدعاء ثانٍ

            # يجب أن يُستدعى مرة واحدة فقط
            assert mock_registry.return_value.register_all_tools.call_count == 1

    async def test_call_tool(self, project_root):
        """اختبار استدعاء أداة."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_registry.return_value.execute_tool = AsyncMock(
                return_value={"success": True, "result": {"value": 42}}
            )
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            result = await server.call_tool("test_tool", {"x": 10})

            assert result["success"] is True
            assert result["result"]["value"] == 42

    async def test_get_resource(self, project_root):
        """اختبار الحصول على مورد."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}
            mock_provider.return_value.get_resource = AsyncMock(return_value={"structure": "data"})

            server = MCPServer(project_root)
            result = await server.get_resource("project://structure")

            assert result["structure"] == "data"

    async def test_get_project_metrics(self, project_root):
        """اختبار الحصول على إحصائيات المشروع."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_registry.return_value.execute_tool = AsyncMock(
                return_value={"success": True, "result": {"files": 100}}
            )
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            await server.get_project_metrics()

            mock_registry.return_value.execute_tool.assert_called_with("get_project_metrics", {})

    async def test_analyze_file(self, project_root):
        """اختبار تحليل ملف."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_registry.return_value.execute_tool = AsyncMock(
                return_value={"success": True, "result": {"analyzed": True}}
            )
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            await server.analyze_file("app/main.py")

            mock_registry.return_value.execute_tool.assert_called_with(
                "analyze_file", {"file_path": "app/main.py"}
            )

    async def test_search_codebase(self, project_root):
        """اختبار البحث في الكود."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_registry.return_value.execute_tool = AsyncMock(
                return_value={"success": True, "result": {"matches": []}}
            )
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            await server.search_codebase("test query", "semantic")

            mock_registry.return_value.execute_tool.assert_called_with(
                "search_codebase", {"query": "test query", "search_type": "semantic"}
            )

    def test_list_tools(self, project_root):
        """اختبار قائمة الأدوات."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider"),
        ):
            mock_registry.return_value.list_tools = MagicMock(
                return_value=[{"name": "tool1", "description": "Test"}]
            )

            server = MCPServer(project_root)
            tools = server.list_tools()

            assert len(tools) == 1
            assert tools[0]["name"] == "tool1"

    def test_list_resources(self, project_root):
        """اختبار قائمة الموارد."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry"),
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_provider.return_value.list_resources = MagicMock(
                return_value=[{"uri": "project://test", "name": "Test"}]
            )

            server = MCPServer(project_root)
            resources = server.list_resources()

            assert len(resources) == 1
            assert resources[0]["uri"] == "project://test"

    async def test_shutdown(self, project_root):
        """اختبار إيقاف الخادم."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            await server.initialize()

            assert server._initialized is True

            await server.shutdown()

            assert server._initialized is False

    async def test_get_tools_for_llm(self, project_root):
        """اختبار الحصول على مخطط الأدوات للـ LLM."""
        from app.services.mcp.server import MCPServer

        with (
            patch("app.services.mcp.server.MCPToolRegistry") as mock_registry,
            patch("app.services.mcp.server.MCPResourceProvider") as mock_provider,
        ):
            mock_registry.return_value.register_all_tools = AsyncMock()
            mock_registry.return_value.tools = {}
            mock_registry.return_value.get_openai_schema = MagicMock(
                return_value=[{"type": "function", "function": {"name": "test"}}]
            )
            mock_provider.return_value.initialize = AsyncMock()
            mock_provider.return_value.resources = {}

            server = MCPServer(project_root)
            schema = await server.get_tools_for_llm()

            assert len(schema) == 1
            assert schema[0]["type"] == "function"


class TestGetMCPServer:
    """اختبارات دالة get_mcp_server (Singleton)."""

    def test_returns_same_instance(self, tmp_path):
        """إرجاع نفس النسخة."""
        from app.services.mcp import server as server_module

        # إعادة تعيين الـ singleton
        server_module._mcp_server = None

        with patch.object(server_module, "MCPServer") as mock_server:
            mock_server.return_value = MagicMock()

            server1 = server_module.get_mcp_server(tmp_path)
            server2 = server_module.get_mcp_server(tmp_path)

            assert server1 is server2
            assert mock_server.call_count == 1

        # تنظيف
        server_module._mcp_server = None
