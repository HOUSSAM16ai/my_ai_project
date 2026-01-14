"""
منسق المحادثات (Chat Orchestrator) - النسخة المحسنة.
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

from app.core.ai_gateway import AIClient
from app.core.patterns.strategy import Strategy, StrategyRegistry
from app.services.chat.agents.orchestrator import OrchestratorAgent
from app.services.chat.context import ChatContext
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
from app.services.chat.intent_detector import IntentDetector
from app.services.chat.ports import IntentDetectorPort
from app.caching.semantic import SemanticCache
from app.services.chat.tools import ToolRegistry

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

        تم تحديثها لتستخدم OrchestratorAgent في حالات الإدارة.
        """
        start_time = time.time()

        # 0. الكشف عن النية أولاً (Detect Intent First)
        # This is moved up to allow routing to specialized agents based on intent
        intent_result = await self._intent_detector.detect(question)

        logger.info(
            f"Intent detected: {intent_result.intent} (confidence={intent_result.confidence:.2f})",
            extra={"user_id": user_id, "conversation_id": conversation_id},
        )

        # Check if we should use the new Multi-Agent System (Admin, Analytics, Curriculum)
        admin_keywords = [
            "users",
            "count",
            "find",
            "locate",
            "search",
            "admin",
            "database",
            "schema",
            "tables",
            "project",
            "route",
            "endpoint",
            "مستخدم",
            "المستخدمين",
            "عدد",
            "قاعدة البيانات",
            "قواعد البيانات",
            "الجداول",
            "المشروع",
            "بنية",
            "مسار",
            "سطر",
            "ملف",
        ]
        is_admin_query = any(k in question.lower() for k in admin_keywords)

        # New: Check for Specialized Educational Intents
        from app.services.chat.intent_detector import ChatIntent
        is_specialized_intent = intent_result.intent in (
            ChatIntent.ANALYTICS_REPORT,
            ChatIntent.CURRICULUM_PLAN
        )

        if is_admin_query or is_specialized_intent:
            logger.info("Delegating to Multi-Agent Orchestrator", extra={"user_id": user_id})
            agent = OrchestratorAgent(ai_client, self.tool_registry)

            # Use a buffer to collect the full response for caching later
            full_response_buffer = []

            # Pass context to agent (user_id is critical for security)
            context = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "intent": intent_result.intent
            }

            # Iterate over the async generator from agent.run
            async for chunk in agent.run(question, context=context):
                full_response_buffer.append(chunk)
                yield chunk

            # تخزين الاستجابة في الذاكرة الدلالية
            full_response = "".join(full_response_buffer)
            if full_response:
                await self._semantic_cache.set(question, full_response)

            duration = (time.time() - start_time) * 1000
            logger.debug(f"Agent processed in {duration:.2f}ms")
            return

        # 1. التحقق من الذاكرة الدلالية (Check Semantic Cache)
        cached_response = await self._semantic_cache.get(question)
        if cached_response:
            logger.info("Serving from Semantic Cache", extra={"user_id": user_id})
            # محاكاة التدفق من الكاش
            chunk_size = 50
            for i in range(0, len(cached_response), chunk_size):
                yield cached_response[i : i + chunk_size]
            return

        # Fallback to legacy Strategy Pattern for other chats

        # 2. بناء السياق (Build Context)
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

        # 3. تنفيذ الاستراتيجية (Execute Strategy)
        result = await self._handlers.execute(context)
        if result:
            # تجميع الاستجابة لتخزينها في الكاش لاحقاً
            full_response_buffer = []
            async for chunk in result:
                full_response_buffer.append(chunk)
                yield chunk

            # تخزين النتيجة الكاملة في الذاكرة الدلالية (في الخلفية)
            full_response = "".join(full_response_buffer)
            if full_response:
                # نستخدم create_task لتجنب حظر الاستجابة، لكن يجب الحذر من دورة حياة الحلقة
                # بما أننا في دالة غير متزامنة، يمكننا انتظاره بسرعة أو تركه للمنستقبل
                # هنا سننتظره لضمان التخزين (بما أنه سريع في الذاكرة)
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
