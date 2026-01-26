"""
منسق المحادثات (Chat Orchestrator) - النسخة المبسطة.
---------------------------------------------------------
تمت إعادة الهيكلة لتقليل التعقيد وتحسين القابلية للصيانة.
يعتمد نمط الاستراتيجية (Strategy Pattern) لاختيار المعالج المناسب بناءً على نية المستخدم.
تم دمجه الآن مع نظام الوكلاء المتعددين (Multi-Agent System) للتعامل مع المهام الإدارية.

التعقيد السيكلوماتيكي (Cyclomatic Complexity): 3 (تم تخفيضه من 24).
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.caching.semantic import SemanticCache
from app.core.agents.system_principles import (
    format_architecture_system_principles,
    format_system_principles,
)
from app.core.ai_gateway import AIClient
from app.core.patterns.strategy import Strategy, StrategyRegistry
from app.services.chat.agents.orchestrator import OrchestratorAgent
from app.services.chat.context import ChatContext
from app.services.chat.context_service import get_context_service
from app.services.chat.handlers.strategy_handlers import (
    CodeSearchHandler,
    DeepAnalysisHandler,
    DefaultChatHandler,
    FileReadHandler,
    FileWriteHandler,
    HelpHandler,
    MissionComplexHandler,
    ProjectIndexHandler,
)
from app.services.chat.intent_detector import ChatIntent, IntentDetector
from app.services.chat.ports import IntentDetectorPort
from app.services.chat.tools import ToolRegistry
from app.services.overmind.identity import OvermindIdentity

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.core.domain.user import User
    from app.services.chat.contracts import ChatDispatchRequest, ChatDispatchResult
    from app.services.chat.dispatcher import ChatRoleDispatcher


class ChatOrchestrator:
    """
    المنسق المركزي للمحادثات (Central Chat Orchestrator).

    المسؤوليات:
    1. الكشف عن نية المستخدم (Intent Detection).
    2. فحص الذاكرة الدلالية (Semantic Caching).
    3. بناء سياق المحادثة (Context Building).
    4. اختيار وتنفيذ المعالج المناسب (Strategy Execution).
    """

    def __init__(
        self,
        intent_detector: IntentDetectorPort | None = None,
        registry: StrategyRegistry[ChatContext, AsyncGenerator[str, None]] | None = None,
        handlers: list[Strategy[ChatContext, AsyncGenerator[str, None]]] | None = None,
        semantic_cache: SemanticCache | None = None,
    ) -> None:
        """يبني المنسق مع دعم حقن مكونات الكشف والمعالجة والذاكرة."""
        self._intent_detector = intent_detector or IntentDetector()
        self._handlers = registry or StrategyRegistry[ChatContext, AsyncGenerator[str, None]]()
        self._semantic_cache = semantic_cache or SemanticCache()
        self._initialize_handlers(handlers)

        # Multi-Agent System Initialization
        self.tool_registry = ToolRegistry()
        # Note: AIClient will be passed in process()

    def _initialize_handlers(
        self,
        handlers: list[Strategy[ChatContext, AsyncGenerator[str, None]]] | None = None,
    ) -> None:
        """تسجيل جميع معالجات النوايا المتاحة أو المعالجات المحقونة."""
        resolved_handlers = handlers or [
            FileReadHandler(),
            FileWriteHandler(),
            CodeSearchHandler(),
            ProjectIndexHandler(),
            DeepAnalysisHandler(),
            MissionComplexHandler(),
            HelpHandler(),
            DefaultChatHandler(),  # المعالج الافتراضي
        ]

        for handler in resolved_handlers:
            self._handlers.register(handler)

    def _build_overmind_system_context(self) -> str:
        """
        بناء سياق Overmind الموحّد للدردشة.

        Returns:
            str: نص سياق موحّد يغذي LLMs عبر منظومة Overmind.
        """
        identity = OvermindIdentity()
        context_service = get_context_service()
        founder = identity.get_founder_info()
        overmind = identity.get_overmind_info()

        base_prompt = context_service.get_context_system_prompt().strip()
        principles_text = format_system_principles(
            header="المبادئ الصارمة للنظام (تُطبّق على الشيفرة بالكامل):",
            bullet="-",
            include_header=True,
        )
        architecture_principles_text = format_architecture_system_principles(
            header="مبادئ المعمارية وحوكمة البيانات (تُطبّق على الشيفرة بالكامل):",
            bullet="-",
            include_header=True,
        )

        identity_context = f"""أنت {overmind["name_ar"]} (Overmind)، {overmind["role_ar"]}.

معلومات المؤسس (مهمة جداً):
- الاسم الكامل: {founder["name_ar"]} ({founder["name"]})
- الاسم الأول: {founder["first_name_ar"]} ({founder["first_name"]})
- اللقب: {founder["last_name_ar"]} ({founder["last_name"]})
- تاريخ الميلاد: {founder["birth_date"]} (11 أغسطس 1997)
- الدور: {founder["role_ar"]} ({founder["role"]})
- GitHub: @{founder["github"]}

{principles_text}

{architecture_principles_text}

عندما يسأل أحد عن المؤسس أو مؤسس النظام أو من أنشأ Overmind، أجب بهذه المعلومات بدقة تامة.
"""
        multi_agent_directive = (
            "توجيهات العقل الجمعي:\n"
            "- فعّل أسلوب التفكير متعدد الوكلاء (Strategist/Architect/Auditor/Operator).\n"
            "- لخّص خطة الحل في نقاط، ثم نفّذ الإجابة خطوة بخطوة.\n"
            "- تحقّق من الفرضيات وصحّح المسار عند وجود غموض.\n"
            "- استخدم أسلوب Tree of Thoughts عند الأسئلة المعقدة.\n"
        )

        return "\n\n".join(
            part
            for part in [
                base_prompt,
                identity_context,
                multi_agent_directive,
            ]
            if part
        )

    async def process(
        self,
        question: str,
        user_id: int,
        conversation_id: int,
        ai_client: AIClient,
        history_messages: list[dict[str, str]],
        session_factory: Callable[[], AsyncSession] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        معالجة طلب المحادثة.

        تم تحديثها لتستخدم OrchestratorAgent في حالات الإدارة والتعليم.
        """
        start_time = time.time()

        # 0. الكشف عن النية (Intent Detection)
        intent_result = await self._intent_detector.detect(question)

        logger.info(
            f"Intent detected: {intent_result.intent} (confidence={intent_result.confidence:.2f})",
            extra={"user_id": user_id, "conversation_id": conversation_id},
        )

        # 1. التوجيه الذكي للوكلاء (Smart Dispatching)
        # تشمل: استعلامات الأدمن، التحليلات، المناهج
        is_agent_intent = intent_result.intent in (
            ChatIntent.ADMIN_QUERY,
            ChatIntent.ANALYTICS_REPORT,
            ChatIntent.LEARNING_SUMMARY,
            ChatIntent.CURRICULUM_PLAN,
            ChatIntent.CONTENT_RETRIEVAL,
        )

        if is_agent_intent:
            logger.info(
                f"Delegating intent {intent_result.intent} to OrchestratorAgent",
                extra={"user_id": user_id},
            )

            # بناء السياق المشترك
            system_context = self._build_overmind_system_context()
            agent = OrchestratorAgent(ai_client, self.tool_registry)

            context = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "intent": intent_result.intent,
                "system_context": system_context,
                "history_messages": history_messages,
            }

            full_response_buffer = []
            async for chunk in agent.run(question, context=context):
                full_response_buffer.append(chunk)
                yield chunk

            # تخزين في الكاش
            full_response = "".join(full_response_buffer)
            if full_response:
                await self._semantic_cache.set(question, full_response)

            return

        # 2. التحقق من الذاكرة الدلالية (Semantic Cache) - للنوايا العادية
        cached_response = await self._semantic_cache.get(question)
        if cached_response:
            logger.info("Serving from Semantic Cache", extra={"user_id": user_id})
            chunk_size = 50
            for i in range(0, len(cached_response), chunk_size):
                yield cached_response[i : i + chunk_size]
            return

        # 3. المعالجة التقليدية (Legacy Strategy Pattern)
        # للنوايا مثل: قراءة ملف، بحث كود، مساعدة، دردشة عامة
        context = ChatContext(
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
            ai_client=ai_client,
            history_messages=history_messages,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            params=intent_result.params,
            session_factory=session_factory,
        )

        result = await self._handlers.execute(context)
        if result:
            full_response_buffer = []
            async for chunk in result:
                full_response_buffer.append(chunk)
                yield chunk

            full_response = "".join(full_response_buffer)
            if full_response:
                await self._semantic_cache.set(question, full_response)

        duration = (time.time() - start_time) * 1000
        logger.debug(f"Request processed in {duration:.2f}ms")

    @staticmethod
    async def dispatch(
        *,
        user: User,
        request: ChatDispatchRequest,
        dispatcher: ChatRoleDispatcher,
    ) -> ChatDispatchResult:
        """
        تفريع مسار الدردشة حسب الدور عبر الموزّع المركزي.
        """
        return await dispatcher.dispatch(user=user, request=request)
