"""
منسق المحادثات (Chat Orchestrator) - النسخة المحسنة.
---------------------------------------------------------
تمت إعادة الهيكلة لتقليل التعقيد وتحسين القابلية للصيانة.
يعتمد نمط الاستراتيجية (Strategy Pattern) لاختيار المعالج المناسب بناءً على نية المستخدم.

التعقيد السيكلوماتيكي (Cyclomatic Complexity): 3 (تم تخفيضه من 24).
"""

import logging
import time
from collections.abc import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.patterns.strategy import StrategyRegistry
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

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    """
    المنسق المركزي للمحادثات (Central Chat Orchestrator).

    المسؤوليات:
    1. الكشف عن نية المستخدم (Intent Detection).
    2. بناء سياق المحادثة (Context Building).
    3. اختيار وتنفيذ المعالج المناسب (Strategy Execution).
    """

    def __init__(self) -> None:
        self._intent_detector = IntentDetector()
        self._handlers = StrategyRegistry[ChatContext, AsyncGenerator[str, None]]()
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """تسجيل جميع معالجات النوايا المتاحة."""
        handlers = [
            FileReadHandler(),
            FileWriteHandler(),
            CodeSearchHandler(),
            ProjectIndexHandler(),
            DeepAnalysisHandler(),
            MissionComplexHandler(),
            HelpHandler(),
            DefaultChatHandler(),  # المعالج الافتراضي
        ]

        for handler in handlers:
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

        Args:
            question: سؤال المستخدم.
            user_id: معرف المستخدم.
            conversation_id: معرف المحادثة.
            ai_client: عميل الذكاء الاصطناعي.
            history_messages: سجل الرسائل السابق.
            session_factory: مصنع الجلسات للعمليات الخلفية.

        Yields:
            str: أجزاء الرد (Chunks) بشكل تدفقي.
        """
        start_time = time.time()

        # 1. الكشف عن النية (Detect Intent)
        intent_result = await self._intent_detector.detect(question)

        logger.info(
            f"Intent detected: {intent_result.intent} (confidence={intent_result.confidence:.2f})",
            extra={"user_id": user_id, "conversation_id": conversation_id},
        )

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
            async for chunk in result:
                yield chunk

        duration = (time.time() - start_time) * 1000
        logger.debug(f"Request processed in {duration:.2f}ms")
