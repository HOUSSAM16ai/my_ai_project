"""
اختبارات شاملة لـ MCP Integrations.
==================================

يغطي:
- تكامل LangGraph
- تكامل LlamaIndex
- تكامل DSPy
- تكامل Reranker
- تكامل Kagent
- حالة جميع التكاملات
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPIntegrationsLangGraph:
    """اختبارات تكامل LangGraph."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        """إنشاء MCPIntegrations للاختبارات."""
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    async def test_run_langgraph_workflow_success(self, integrations):
        """تشغيل سير عمل LangGraph بنجاح."""
        with patch("app.services.mcp.integrations.LangGraphAgentService") as MockService, \
             patch("app.services.mcp.integrations.LangGraphRunRequest"):
            
            mock_result = MagicMock()
            mock_result.run_id = "run-123"
            mock_result.final_answer = "تم الإنجاز"
            mock_result.steps = ["step1", "step2"]
            
            MockService.return_value.run = AsyncMock(return_value=mock_result)
            
            result = await integrations.run_langgraph_workflow(
                goal="تحليل الكود",
                context={"file": "test.py"},
            )
            
            assert result["success"] is True
            assert result["run_id"] == "run-123"
            assert result["final_answer"] == "تم الإنجاز"
    
    async def test_run_langgraph_workflow_error(self, integrations):
        """معالجة خطأ في LangGraph."""
        with patch(
            "app.services.mcp.integrations.LangGraphAgentService",
            side_effect=Exception("Service unavailable"),
        ):
            result = await integrations.run_langgraph_workflow(goal="test")
            
            assert result["success"] is False
            assert "Service unavailable" in result["error"]
    
    def test_get_langgraph_status_active(self, integrations):
        """حالة LangGraph نشطة."""
        with patch("app.services.mcp.integrations.LangGraphAgentService"):
            status = integrations.get_langgraph_status()
            
            assert status["status"] == "active"
            assert "agents" in status
    
    def test_get_langgraph_status_unavailable(self, integrations):
        """حالة LangGraph غير متوفرة."""
        with patch(
            "app.services.mcp.integrations.LangGraphAgentService",
            side_effect=ImportError("Module not found"),
        ):
            status = integrations.get_langgraph_status()
            
            assert status["status"] == "unavailable"


class TestMCPIntegrationsLlamaIndex:
    """اختبارات تكامل LlamaIndex."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    async def test_semantic_search_success(self, integrations):
        """بحث دلالي ناجح."""
        with patch("app.services.mcp.integrations.get_retriever") as mock_get:
            mock_retriever = MagicMock()
            mock_retriever.search = AsyncMock(return_value=["result1", "result2"])
            mock_get.return_value = mock_retriever
            
            result = await integrations.semantic_search(
                query="احتمالات",
                top_k=5,
            )
            
            assert result["success"] is True
            assert result["count"] == 2
    
    async def test_semantic_search_error(self, integrations):
        """معالجة خطأ في البحث الدلالي."""
        with patch(
            "app.services.mcp.integrations.get_retriever",
            side_effect=Exception("DB connection failed"),
        ):
            result = await integrations.semantic_search(query="test")
            
            assert result["success"] is False
            assert "DB connection failed" in result["error"]
    
    def test_get_llamaindex_status_active(self, integrations):
        """حالة LlamaIndex نشطة."""
        with patch("app.services.mcp.integrations.LlamaIndexRetriever"):
            status = integrations.get_llamaindex_status()
            
            assert status["status"] == "active"
            assert "capabilities" in status


class TestMCPIntegrationsDSPy:
    """اختبارات تكامل DSPy."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    async def test_refine_query_success(self, integrations):
        """تحسين استعلام بنجاح."""
        with patch("app.services.mcp.integrations.get_refined_query") as mock_refine:
            mock_refine.return_value = {
                "refined_query": "الاحتمالات في الرياضيات",
                "year": 2024,
                "subject": "رياضيات",
                "branch": None,
            }
            
            result = await integrations.refine_query(
                query="احتمالات 2024",
                api_key="test-key",
            )
            
            assert result["success"] is True
            assert result["original_query"] == "احتمالات 2024"
            assert result["extracted_filters"]["year"] == 2024
    
    async def test_generate_plan_success(self, integrations):
        """توليد خطة بنجاح."""
        with patch("app.services.mcp.integrations.PlanGenerator") as MockGen:
            mock_result = MagicMock()
            mock_result.plan_steps = ["خطوة 1", "خطوة 2", "خطوة 3"]
            MockGen.return_value.forward = MagicMock(return_value=mock_result)
            
            result = await integrations.generate_plan(
                goal="تحسين الأداء",
                context="تطبيق ويب",
            )
            
            assert result["success"] is True
            assert len(result["plan_steps"]) == 3
    
    def test_get_dspy_status_active(self, integrations):
        """حالة DSPy نشطة."""
        with patch.dict("sys.modules", {"dspy": MagicMock()}):
            status = integrations.get_dspy_status()
            
            assert status["status"] == "active"
            assert "modules" in status


class TestMCPIntegrationsReranker:
    """اختبارات تكامل Reranker."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    async def test_rerank_results_success(self, integrations):
        """إعادة ترتيب النتائج بنجاح."""
        with patch("app.services.mcp.integrations.get_reranker") as mock_get:
            mock_reranker = MagicMock()
            mock_reranker.rerank = MagicMock(
                return_value=["doc2", "doc1", "doc3"]
            )
            mock_get.return_value = mock_reranker
            
            result = await integrations.rerank_results(
                query="احتمالات",
                documents=["doc1", "doc2", "doc3"],
                top_n=3,
            )
            
            assert result["success"] is True
            assert result["reranked_results"][0] == "doc2"
    
    async def test_rerank_results_error(self, integrations):
        """معالجة خطأ في إعادة الترتيب."""
        with patch(
            "app.services.mcp.integrations.get_reranker",
            side_effect=Exception("Model not loaded"),
        ):
            result = await integrations.rerank_results(
                query="test",
                documents=["doc1"],
            )
            
            assert result["success"] is False
            assert "Model not loaded" in result["error"]


class TestMCPIntegrationsKagent:
    """اختبارات تكامل Kagent."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    async def test_execute_action_success(self, integrations):
        """تنفيذ إجراء بنجاح."""
        with patch("app.services.mcp.integrations.KagentMesh") as MockMesh, \
             patch("app.services.mcp.integrations.AgentRequest"):
            
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.result = {"output": "done"}
            mock_response.error = None
            
            MockMesh.return_value.execute_action = AsyncMock(
                return_value=mock_response
            )
            
            result = await integrations.execute_action(
                action="analyze",
                capability="code_analysis",
                payload={"file": "test.py"},
            )
            
            assert result["success"] is True
            assert result["result"]["output"] == "done"
    
    async def test_execute_action_error(self, integrations):
        """معالجة خطأ في تنفيذ الإجراء."""
        with patch(
            "app.services.mcp.integrations.KagentMesh",
            side_effect=Exception("Mesh unavailable"),
        ):
            result = await integrations.execute_action(
                action="test",
                capability="test",
            )
            
            assert result["success"] is False
            assert "Mesh unavailable" in result["error"]
    
    def test_get_kagent_status_active(self, integrations):
        """حالة Kagent نشطة."""
        with patch("app.services.mcp.integrations.KagentMesh"):
            status = integrations.get_kagent_status()
            
            assert status["status"] == "active"
            assert "components" in status


class TestMCPIntegrationsStatus:
    """اختبارات حالة جميع التكاملات."""
    
    @pytest.fixture
    def integrations(self, tmp_path):
        from app.services.mcp.integrations import MCPIntegrations
        return MCPIntegrations(project_root=tmp_path)
    
    def test_get_all_integrations_status(self, integrations):
        """الحصول على حالة جميع التكاملات."""
        with patch.object(
            integrations, "get_langgraph_status",
            return_value={"status": "active"},
        ), patch.object(
            integrations, "get_llamaindex_status",
            return_value={"status": "active"},
        ), patch.object(
            integrations, "get_dspy_status",
            return_value={"status": "active"},
        ), patch.object(
            integrations, "get_reranker_status",
            return_value={"status": "active"},
        ), patch.object(
            integrations, "get_kagent_status",
            return_value={"status": "active"},
        ):
            status = integrations.get_all_integrations_status()
            
            assert "langgraph" in status
            assert "llamaindex" in status
            assert "dspy" in status
            assert "reranker" in status
            assert "kagent" in status
            
            assert all(s["status"] == "active" for s in status.values())
