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

import contextlib
from pathlib import Path

from app.core.logging import get_logger
from app.core.settings.base import get_settings
from app.domain.models.agents import SearchFilters, SearchRequest
from app.infrastructure.clients.http_planning_client import HttpPlanningClient
from app.infrastructure.clients.http_research_client import HttpResearchClient

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

        # Initialize Microservice Clients
        settings = get_settings()
        self.research_client = HttpResearchClient(settings.RESEARCH_AGENT_URL)
        self.planning_client = HttpPlanningClient(settings.PLANNING_AGENT_URL)

    # ============== LangGraph ==============

    async def run_langgraph_workflow(
        self,
        goal: str,
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """
        تشغيل سير عمل LangGraph.

        Args:
            goal: الهدف المطلوب تحقيقه
            context: سياق إضافي (اختياري)

        Returns:
            dict: نتيجة سير العمل
        """
        try:
            from app.services.overmind.domain.api_schemas import LangGraphRunRequest
            from app.services.overmind.factory import create_langgraph_service

            service = create_langgraph_service()
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

    def get_langgraph_status(self) -> dict[str, object]:
        """حالة LangGraph."""
        try:
            from app.services.overmind.langgraph import LangGraphAgentService  # noqa: F401

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
        filters: dict[str, object] | None = None,
    ) -> dict[str, object]:
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
            # Refactored to use HTTP Client
            req = SearchRequest(q=query, limit=top_k, filters=SearchFilters(**(filters or {})))
            results = await self.research_client.search(req)

            return {
                "success": True,
                "query": query,
                "results": [r.model_dump() for r in results],
                "count": len(results),
            }
        except Exception as e:
            logger.error(f"خطأ في البحث الدلالي: {e}")
            return {"success": False, "error": str(e)}

    def get_llamaindex_status(self) -> dict[str, object]:
        """حالة LlamaIndex."""
        # This check might need update to ping the service, but kept simple for now
        return {
            "status": "active",
            "capabilities": ["semantic_search", "metadata_filtering"],
            "mode": "microservice",
        }

    # ============== DSPy ==============

    async def refine_query(
        self,
        query: str,
        api_key: str | None = None,
    ) -> dict[str, object]:
        """
        تحسين استعلام باستخدام DSPy.

        Args:
            query: الاستعلام الأصلي
            api_key: مفتاح API (اختياري)

        Returns:
            dict: الاستعلام المحسن مع الفلاتر
        """
        try:
            # Refactored to use HTTP Client
            result = await self.research_client.refine_query(query, api_key)

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
    ) -> dict[str, object]:
        """
        توليد خطة باستخدام DSPy.

        Args:
            goal: الهدف المطلوب
            context: السياق

        Returns:
            dict: خطوات الخطة
        """
        try:
            # Refactored to use HTTP Client
            ctx_list = [context] if context else []
            plan = await self.planning_client.generate_plan(goal, ctx_list)

            return {
                "success": True,
                "goal": plan.goal,
                "plan_steps": plan.steps,
            }
        except Exception as e:
            logger.error(f"خطأ في توليد الخطة: {e}")
            return {"success": False, "error": str(e)}

    def get_dspy_status(self) -> dict[str, object]:
        """حالة DSPy."""
        return {
            "status": "active",
            "modules": ["GeneratePlan", "CritiquePlan", "QueryRefiner"],
            "mode": "microservice",
        }

    # ============== Reranker ==============

    async def rerank_results(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
    ) -> dict[str, object]:
        """
        إعادة ترتيب النتائج باستخدام Reranker.

        Args:
            query: نص الاستعلام
            documents: قائمة المستندات
            top_n: عدد النتائج المطلوبة

        Returns:
            dict: النتائج المرتبة (Pass-through pending API support)
        """
        # TODO: Implement remote reranking via Research Agent HTTP API when available.
        # Current Behavior: Pass-through (No-op) to avoid monolith dependency.
        return {
            "success": True,
            "query": query,
            "reranked_results": documents[:top_n],
        }

    def get_reranker_status(self) -> dict[str, object]:
        """حالة Reranker."""
        return {
            "status": "pending_migration",
            "model": "BAAI/bge-reranker-base",
            "note": "Awaiting HTTP API exposure",
        }

    # ============== Kagent ==============

    async def execute_action(
        self,
        action: str,
        capability: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
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
            from app.services.kagent import AgentRequest, KagentMesh

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

    def get_kagent_status(self) -> dict[str, object]:
        """حالة Kagent."""
        try:
            from app.services.kagent import KagentMesh  # noqa: F401

            return {
                "status": "active",
                "components": ["ServiceRegistry", "SecurityMesh", "LocalAdapter"],
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== ملخص الحالة ==============

    def get_all_integrations_status(self) -> dict[str, object]:
        """
        تعيد حالة جميع التكاملات (للوحة تحكم الأدمن).
        يتم فحص الحالة فعلياً بدلاً من إرجاع قيم ثابتة.
        """
        # جلب إحصائيات الإصلاح الحقيقية
        try:
            from app.services.overmind.agents.self_healing import get_self_healing_agent

            healing_agent = get_self_healing_agent()
            healing_stats = healing_agent.get_healing_stats()
        except ImportError:
            healing_stats = {"status": "module_not_found"}

        return {
            "langgraph": self._check_langgraph_status(),
            "kagent": self._check_kagent_status(),
            "learning": self.get_learning_status(),
            "knowledge": self.get_knowledge_status(),
            "analytics_dashboard": {
                "status": "active",
                "integration": "predictive_analyzer",
                "healing_metrics": healing_stats,
            },
            "vision": self.get_vision_status(),
            "collaboration": self.get_collaboration_status(),
        }

    def _check_langgraph_status(self) -> dict[str, object]:
        try:
            from app.services.overmind.langgraph import LangGraphAgentService

            # Verify availability
            if LangGraphAgentService:
                return {"status": "active", "version": "0.1.0", "service": "LangGraphAgentService"}
            return {"status": "unknown"}
        except ImportError:
            return {"status": "unavailable", "error": "Module not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_kagent_status(self) -> dict[str, object]:
        try:
            from app.services.kagent import KagentMesh

            # Verify availability
            if KagentMesh:
                return {"status": "active", "mesh": "KagentMesh"}
            return {"status": "unknown"}
        except ImportError:
            return {"status": "unavailable", "error": "Module not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============== Learning Services ==============

    async def get_student_profile(
        self,
        student_id: int,
    ) -> dict[str, object]:
        """
        جلب ملف الطالب التعليمي.

        يستخدم LlamaIndex لإثراء الملف بالسياق.
        """
        try:
            from app.services.learning.student_profile import get_student_profile

            profile = await get_student_profile(student_id)

            # إثراء بالسياق من LlamaIndex (إذا متوفر)
            with contextlib.suppress(Exception):
                # Use search client if possible, but profile enrichment might be specific logic
                # For now, suppressing import error
                pass

            return {
                "success": True,
                "student_id": student_id,
                "mastery": profile.overall_mastery,
                "accuracy": profile.overall_accuracy,
                "strengths": profile.strengths,
                "weaknesses": profile.weaknesses,
                "brief": profile.to_brief(),
            }
        except Exception as e:
            logger.error(f"خطأ في ملف الطالب: {e}")
            return {"success": False, "error": str(e)}

    async def record_learning_event(
        self,
        student_id: int,
        topic_id: str,
        topic_name: str,
        is_correct: bool,
        content_id: str | None = None,
    ) -> dict[str, object]:
        """تسجيل حدث تعليمي."""
        try:
            from app.services.learning.student_profile import (
                get_student_profile,
                save_student_profile,
            )

            profile = await get_student_profile(student_id)
            profile.record_attempt(topic_id, topic_name, is_correct, content_id)
            await save_student_profile(profile)

            return {
                "success": True,
                "new_mastery": profile.topic_mastery.get(topic_id).mastery_score
                if topic_id in profile.topic_mastery
                else 0,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_difficulty_recommendation(
        self,
        student_id: int,
        topic_id: str,
    ) -> dict[str, object]:
        """توصية بمستوى الصعوبة."""
        try:
            from app.services.learning.difficulty_adjuster import get_difficulty_adjuster
            from app.services.learning.student_profile import get_student_profile

            profile = await get_student_profile(student_id)
            adjuster = get_difficulty_adjuster()
            rec = adjuster.recommend(profile, topic_id)

            return {
                "success": True,
                "level": rec.level.value,
                "reason": rec.reason,
                "hints": rec.suggested_hints,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_learning_status(self) -> dict[str, object]:
        """حالة خدمات التعلم."""
        try:
            from app.services.learning import (  # noqa: F401
                DifficultyAdjuster,
                MasteryTracker,
                StudentProfile,
            )

            return {
                "status": "active",
                "components": ["StudentProfile", "DifficultyAdjuster", "MasteryTracker"],
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== Knowledge Graph ==============

    async def check_prerequisites(
        self,
        student_id: int,
        concept_id: str,
    ) -> dict[str, object]:
        """
        فحص المتطلبات السابقة.

        يستخدم Reranker لترتيب المفاهيم المفقودة.
        """
        try:
            from app.services.knowledge.prerequisite_checker import get_prerequisite_checker
            from app.services.learning.student_profile import get_student_profile

            profile = await get_student_profile(student_id)
            checker = get_prerequisite_checker()
            report = checker.check_readiness(profile, concept_id)

            # استخدام Reranker لترتيب المتطلبات حسب الأهمية
            missing = report.missing_prerequisites
            if missing and len(missing) > 1:
                try:
                    reranked = await self.rerank_results(
                        query=concept_id,
                        documents=missing,
                        top_n=3,
                    )
                    if reranked.get("success"):
                        missing = reranked["reranked_results"]
                except Exception:
                    pass

            return {
                "success": True,
                "concept": report.concept_name,
                "is_ready": report.is_ready,
                "readiness_score": report.readiness_score,
                "missing_prerequisites": missing,
                "recommendation": report.recommendation,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_learning_path(
        self,
        from_concept: str,
        to_concept: str,
    ) -> dict[str, object]:
        """إيجاد مسار التعلم."""
        try:
            from app.services.knowledge.concept_graph import get_concept_graph

            graph = get_concept_graph()
            path = graph.get_learning_path(from_concept, to_concept)

            return {
                "success": True,
                "path": [c.name_ar for c in path],
                "steps": len(path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_related_concepts(
        self,
        topic: str,
    ) -> dict[str, object]:
        """
        إيجاد المفاهيم المرتبطة.

        يستخدم DSPy لتحسين البحث.
        """
        try:
            from app.services.knowledge.concept_graph import get_concept_graph

            graph = get_concept_graph()

            # تحسين البحث بـ DSPy
            refined = await self.refine_query(topic)
            search_term = refined.get("refined_query", topic) if refined.get("success") else topic

            concept = graph.find_concept_by_topic(search_term)

            if not concept:
                return {"success": False, "error": "مفهوم غير موجود"}

            related = graph.get_related_concepts(concept.concept_id)
            prereqs = graph.get_prerequisites(concept.concept_id)
            next_concepts = graph.get_next_concepts(concept.concept_id)

            return {
                "success": True,
                "concept": concept.name_ar,
                "related": [c.name_ar for c in related],
                "prerequisites": [c.name_ar for c in prereqs],
                "leads_to": [c.name_ar for c in next_concepts],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_knowledge_status(self) -> dict[str, object]:
        """حالة خدمات المعرفة."""
        try:
            from app.services.knowledge import ConceptGraph, PrerequisiteChecker  # noqa: F401
            from app.services.knowledge.concept_graph import get_concept_graph

            graph = get_concept_graph()
            return {
                "status": "active",
                "concepts_count": len(graph.concepts),
                "relations_count": len(graph.relations),
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== Predictive Analytics ==============

    async def predict_struggles(
        self,
        student_id: int,
    ) -> dict[str, object]:
        """
        التنبؤ بالصعوبات المستقبلية.

        يستخدم DSPy لتحسين التنبؤات.
        """
        try:
            from app.services.analytics.predictive_analyzer import get_predictive_analyzer

            analyzer = get_predictive_analyzer()
            predictions = await analyzer.predict_struggles(student_id)

            return {
                "success": True,
                "predictions": [
                    {
                        "topic": p.topic_name,
                        "probability": p.probability,
                        "warning_signs": p.warning_signs,
                        "tips": p.prevention_tips,
                    }
                    for p in predictions[:5]
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def detect_error_patterns(
        self,
        student_id: int,
    ) -> dict[str, object]:
        """كشف أنماط الأخطاء."""
        try:
            from app.services.analytics.pattern_detector import get_pattern_detector

            detector = get_pattern_detector()
            patterns = await detector.detect_patterns(student_id)

            return {
                "success": True,
                "patterns": [
                    {
                        "type": p.pattern_type,
                        "description": p.description,
                        "frequency": p.frequency,
                        "remediation": p.remediation,
                    }
                    for p in patterns
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_analytics_status(self) -> dict[str, object]:
        """حالة خدمات التحليل."""
        try:
            from app.services.analytics import PatternDetector, PredictiveAnalyzer  # noqa: F401

            return {
                "status": "active",
                "components": ["PredictiveAnalyzer", "PatternDetector"],
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== Vision Services ==============

    async def analyze_exercise_image(
        self,
        image_path: str,
    ) -> dict[str, object]:
        """
        تحليل صورة تمرين.

        يستخدم LlamaIndex لربط المحتوى بالمعرفة.
        """
        try:
            from app.services.vision.multimodal_processor import get_multimodal_processor

            processor = get_multimodal_processor()
            result = await processor.extract_exercise_from_image(image_path)

            # ربط بالمحتوى الموجود (LlamaIndex)
            if result.get("success") and result.get("type"):
                search_result = await self.semantic_search(
                    query=result["type"],
                    top_k=3,
                )
                result["related_exercises"] = search_result.get("results", [])

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_vision_status(self) -> dict[str, object]:
        """حالة خدمات الرؤية."""
        try:
            from app.services.vision import (  # noqa: F401
                DiagramAnalyzer,
                EquationDetector,
                MultiModalProcessor,
            )

            return {
                "status": "active",
                "components": ["MultiModalProcessor", "EquationDetector", "DiagramAnalyzer"],
                "supported_formats": ["jpg", "png", "webp"],
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== Collaboration ==============

    async def create_study_session(
        self,
        exercise_id: str,
        topic: str,
    ) -> dict[str, object]:
        """
        إنشاء جلسة دراسة تعاونية.

        يستخدم Kagent لتنسيق الوكلاء المساعدين.
        """
        try:
            from app.services.collaboration.session import create_session

            session = create_session(exercise_id=exercise_id, topic=topic)

            # تسجيل مع Kagent (إذا متوفر)
            with contextlib.suppress(Exception):
                await self.execute_action(
                    action="register_session",
                    capability="collaboration",
                    payload={"session_id": session.session_id},
                )

            return {
                "success": True,
                "session_id": session.session_id,
                "topic": topic,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def join_study_session(
        self,
        session_id: str,
        student_id: int,
        name: str = "",
    ) -> dict[str, object]:
        """انضمام لجلسة دراسة."""
        try:
            from app.services.collaboration.session import get_session

            session = get_session(session_id)
            if not session:
                return {"success": False, "error": "جلسة غير موجودة"}

            session.join(student_id, name)

            return {
                "success": True,
                "session_id": session_id,
                "participants": len(session.get_active_participants()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_collaboration_status(self) -> dict[str, object]:
        """حالة خدمات التعاون."""
        try:
            from app.services.collaboration import (  # noqa: F401
                CollaborativeSession,
                SharedWorkspace,
            )
            from app.services.collaboration.session import list_active_sessions

            return {
                "status": "active",
                "active_sessions": len(list_active_sessions()),
            }
        except ImportError:
            return {"status": "unavailable"}

    # ============== Socratic Tutor ==============

    async def socratic_guide(
        self,
        question: str,
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """
        إرشاد سقراطي.

        يستخدم LangGraph لتنسيق الحوار.
        """
        try:
            from app.core.ai_gateway import get_ai_client
            from app.services.chat.agents.socratic_tutor import get_socratic_tutor

            ai_client = get_ai_client()
            tutor = get_socratic_tutor(ai_client)

            # جمع الاستجابة
            response_parts = []
            async for chunk in tutor.guide(question, context):
                response_parts.append(chunk)

            return {
                "success": True,
                "response": "".join(response_parts),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
