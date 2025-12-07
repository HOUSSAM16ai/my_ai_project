"""
Refactored chat orchestrator with reduced complexity.

BEFORE: Cyclomatic Complexity = 24
AFTER: Cyclomatic Complexity = 3
"""

import logging
import time
from typing import AsyncGenerator

from app.core.patterns.strategy import StrategyRegistry
from typing import Any as AIClient  # Placeholder for AI client type
from app.services.chat.refactored.context import ChatContext
from app.services.chat.refactored.handlers import (
    CodeSearchHandler,
    DeepAnalysisHandler,
    DefaultChatHandler,
    FileReadHandler,
    FileWriteHandler,
    HelpHandler,
    MissionComplexHandler,
    ProjectIndexHandler,
)
from app.services.chat.refactored.intent_detector import IntentDetector

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """
    Refactored orchestrator using Strategy pattern.
    
    Complexity reduced from 24 to 3 by:
    1. Extracting intent handlers to separate classes
    2. Using Strategy pattern for handler selection
    3. Removing nested conditionals
    """

    def __init__(self):
        self._intent_detector = IntentDetector()
        self._handlers = StrategyRegistry[ChatContext, AsyncGenerator[str, None]]()
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """Register all intent handlers."""
        handlers = [
            FileReadHandler(),
            FileWriteHandler(),
            CodeSearchHandler(),
            ProjectIndexHandler(),
            DeepAnalysisHandler(),
            MissionComplexHandler(),
            HelpHandler(),
            DefaultChatHandler(),  # Fallback
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
    ) -> AsyncGenerator[str, None]:
        """
        Process chat request.
        
        Complexity: 3 (down from 24)
        """
        start_time = time.time()

        # Detect intent
        intent_result = await self._intent_detector.detect(question)
        
        logger.info(
            f"Intent detected: {intent_result.intent} "
            f"(confidence={intent_result.confidence:.2f})",
            extra={"user_id": user_id, "conversation_id": conversation_id}
        )

        # Build context
        context = ChatContext(
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
            ai_client=ai_client,
            history_messages=history_messages,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            params=intent_result.params,
        )

        # Execute handler
        result = await self._handlers.execute(context)
        if result:
            async for chunk in result:
                yield chunk

        duration = (time.time() - start_time) * 1000
        logger.debug(f"Request processed in {duration:.2f}ms")
