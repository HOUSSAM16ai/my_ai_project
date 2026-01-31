"""
تكاملات MCP مع التقنيات المتقدمة.
==================================

يجمع بين:
- LangGraph للتنسيق
- LlamaIndex للاسترجاع
- DSPy للتحسين
- Reranker للترتيب
- Kagent للتنفيذ

هذا الملف يوفر واجهة موحدة للتكامل مع كل هذه التقنيات.
"""

from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPIntegrations:
    """
    تكاملات MCP مع التقنيات المتقدمة.
    
    يوفر واجهة موحدة للتفاعل مع:
    - LangGraph: تشغيل سير العمل المتعدد الوكلاء
    - LlamaIndex: البحث الدلالي واسترجاع السياق
    - DSPy: تحسين الاستعلامات والتفكير
    - Reranker: إعادة ترتيب النتائج
    - Kagent: تنفيذ الإجراءات عبر الوكلاء
    """
    
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self._langgraph_engine = None
        self._kagent_mesh = None
        self._reranker = None
    
    # ============== LangGraph ==============
    
    async def run_langgraph_workflow(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        تشغيل سير عمل LangGraph.
        
        Args:
            goal: الهدف المطلوب تحقيقه
            context: سياق إضافي (اختياري)
            
        Returns:
            dict: نتيجة سير العمل
        """
        try:
            from app.services.overmind.langgraph import LangGraphAgentService
            from app.services.overmind.domain.api_schemas import LangGraphRunRequest
            
            service = LangGraphAgentService()
            request = LangGraphRunRequest(
                goal=goal,
                context=context or {},
            )
            
            result = await service.run(request)
            
            return {
                "success": True,
                "run_id": result.run_id,
                "final_answer": result.final_answer,
                "steps": result.steps,
            }
        except Exception as e:
            logger.error(f"خطأ في LangGraph: {e}")
            return {"success": False, "error": str(e)}
    
    def get_langgraph_status(self) -> dict[str, Any]:
        """حالة LangGraph."""
        try:
            from app.services.overmind.langgraph import LangGraphAgentService
            return {
                "status": "active",
                "agents": ["contextualizer", "strategist", "architect", "operator", "auditor"],
                "supervisor": "active",
            }
        except ImportError:
            return {"status": "unavailable", "error": "LangGraph غير متوفر"}
    
    # ============== LlamaIndex ==============
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        بحث دلالي باستخدام LlamaIndex.
        
        Args:
            query: نص البحث
            top_k: عدد النتائج
            filters: فلاتر البحث (السنة، الموضوع، الفرع)
            
        Returns:
            dict: نتائج البحث
        """
        try:
            from microservices.research_agent.src.search_engine import (
                get_retriever,
            )
            
            # ملاحظة: قد يحتاج URL قاعدة البيانات
            retriever = get_retriever("postgresql://...")
            results = await retriever.search(query, top_k=top_k, filters=filters)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            logger.error(f"خطأ في LlamaIndex: {e}")
            return {"success": False, "error": str(e)}
    
    def get_llamaindex_status(self) -> dict[str, Any]:
        """حالة LlamaIndex."""
        try:
            from microservices.research_agent.src.search_engine import LlamaIndexRetriever
            return {
                "status": "active",
                "capabilities": ["semantic_search", "metadata_filtering", "reranking"],
            }
        except ImportError:
            return {"status": "unavailable"}
    
    # ============== DSPy ==============
    
    async def refine_query(
        self,
        query: str,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        تحسين استعلام باستخدام DSPy.
        
        Args:
            query: الاستعلام الأصلي
            api_key: مفتاح API (اختياري)
            
        Returns:
            dict: الاستعلام المحسن مع الفلاتر
        """
        try:
            from microservices.research_agent.src.search_engine.query_refiner import (
                get_refined_query,
            )
            
            result = get_refined_query(query, api_key)
            
            return {
                "success": True,
                "original_query": query,
                "refined_query": result.get("refined_query", query),
                "extracted_filters": {
                    "year": result.get("year"),
                    "subject": result.get("subject"),
                    "branch": result.get("branch"),
                },
            }
        except Exception as e:
            logger.error(f"خطأ في DSPy: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_plan(
        self,
        goal: str,
        context: str = "",
    ) -> dict[str, Any]:
        """
        توليد خطة باستخدام DSPy.
        
        Args:
            goal: الهدف المطلوب
            context: السياق
            
        Returns:
            dict: خطوات الخطة
        """
        try:
            from microservices.planning_agent.cognitive import PlanGenerator
            
            generator = PlanGenerator()
            result = generator.forward(goal=goal, context=context)
            
            return {
                "success": True,
                "goal": goal,
                "plan_steps": result.plan_steps,
            }
        except Exception as e:
            logger.error(f"خطأ في توليد الخطة: {e}")
            return {"success": False, "error": str(e)}
    
    def get_dspy_status(self) -> dict[str, Any]:
        """حالة DSPy."""
        try:
            import dspy
            return {
                "status": "active",
                "modules": ["GeneratePlan", "CritiquePlan", "QueryRefiner"],
            }
        except ImportError:
            return {"status": "unavailable"}
    
    # ============== Reranker ==============
    
    async def rerank_results(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
    ) -> dict[str, Any]:
        """
        إعادة ترتيب النتائج باستخدام Reranker.
        
        Args:
            query: نص الاستعلام
            documents: قائمة المستندات
            top_n: عدد النتائج المطلوبة
            
        Returns:
            dict: النتائج المرتبة
        """
        try:
            from microservices.research_agent.src.search_engine.reranker import (
                get_reranker,
            )
            
            reranker = get_reranker()
            reranked = reranker.rerank(query, documents, top_n=top_n)
            
            return {
                "success": True,
                "query": query,
                "reranked_results": reranked,
            }
        except Exception as e:
            logger.error(f"خطأ في Reranker: {e}")
            return {"success": False, "error": str(e)}
    
    def get_reranker_status(self) -> dict[str, Any]:
        """حالة Reranker."""
        try:
            from microservices.research_agent.src.search_engine.reranker import Reranker
            return {
                "status": "active",
                "model": "BAAI/bge-reranker-base",
            }
        except ImportError:
            return {"status": "unavailable"}
    
    # ============== Kagent ==============
    
    async def execute_action(
        self,
        action: str,
        capability: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        تنفيذ إجراء عبر Kagent.
        
        Args:
            action: اسم الإجراء
            capability: القدرة المطلوبة
            payload: بيانات الإجراء
            
        Returns:
            dict: نتيجة التنفيذ
        """
        try:
            from app.services.kagent import KagentMesh, AgentRequest
            
            mesh = KagentMesh()
            request = AgentRequest(
                action=action,
                capability=capability,
                payload=payload or {},
            )
            
            response = await mesh.execute_action(request)
            
            return {
                "success": response.success,
                "result": response.result,
                "error": response.error,
            }
        except Exception as e:
            logger.error(f"خطأ في Kagent: {e}")
            return {"success": False, "error": str(e)}
    
    def get_kagent_status(self) -> dict[str, Any]:
        """حالة Kagent."""
        try:
            from app.services.kagent import KagentMesh
            return {
                "status": "active",
                "components": ["ServiceRegistry", "SecurityMesh", "LocalAdapter"],
            }
        except ImportError:
            return {"status": "unavailable"}
    
    # ============== ملخص الحالة ==============
    
    def get_all_integrations_status(self) -> dict[str, Any]:
        """
        حالة جميع التكاملات.
        
        Returns:
            dict: حالة كل تقنية
        """
        return {
            "langgraph": self.get_langgraph_status(),
            "llamaindex": self.get_llamaindex_status(),
            "dspy": self.get_dspy_status(),
            "reranker": self.get_reranker_status(),
            "kagent": self.get_kagent_status(),
        }
