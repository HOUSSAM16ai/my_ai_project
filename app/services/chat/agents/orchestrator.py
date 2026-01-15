import logging
from collections.abc import AsyncGenerator

from app.core.ai_gateway import AIClient
from app.services.chat.agents.admin import AdminAgent
from app.services.chat.agents.analytics import AnalyticsAgent
from app.services.chat.agents.curriculum import CurriculumAgent
from app.services.chat.context_service import get_context_service
from app.services.chat.intent_detector import ChatIntent, IntentDetector
from app.services.chat.tools import ToolRegistry
from app.services.overmind.agents.memory import MemoryAgent
from app.services.overmind.domain.context import InMemoryCollaborationContext

logger = logging.getLogger("orchestrator-agent")


class OrchestratorAgent:
    """
    الوكيل المنسق (Orchestrator Agent).

    يعمل كنقطة دخول مركزية لتوجيه الطلبات إلى الوكلاء المتخصصين:
    1. AdminAgent: للمهام الإدارية والاستعلامات عن النظام.
    2. AnalyticsAgent: لتحليل الأداء والتقارير.
    3. CurriculumAgent: لإدارة المسار التعليمي.
    4. Fallback (AI): للمحادثات العامة.
    """

    def __init__(self, ai_client: AIClient, tools: ToolRegistry) -> None:
        self.ai_client = ai_client
        self.tools = tools
        self.intent_detector = IntentDetector()

        # Sub-Agents
        # Inject AIClient into AdminAgent for dynamic routing
        self.admin_agent = AdminAgent(tools, ai_client=ai_client)
        self.analytics_agent = AnalyticsAgent(tools, ai_client)
        self.curriculum_agent = CurriculumAgent(tools)
        self.memory_agent = MemoryAgent()

    async def run(self, question: str, context: dict[str, object] | None = None) -> AsyncGenerator[str, None]:
        """
        واجهة موحدة لمعالجة الطلبات.
        يقوم بكشف النية وتوجيه الطلب للوكيل المناسب، ويعيد النتائج كتدفق (Stream).
        """
        logger.info(f"Orchestrator received: {question}")
        normalized = question.strip()
        context = context or {}

        # 1. Intent Detection
        # If intent is already passed in context (from ChatOrchestrator), use it.
        if "intent" in context and isinstance(context["intent"], ChatIntent):
            intent = context["intent"]
        else:
            intent_result = await self.intent_detector.detect(normalized)
            intent = intent_result.intent

        # 2. Memory Capture (Best Effort)
        await self._capture_memory_intent(normalized, intent)

        # 3. Dispatch
        try:
            if intent == ChatIntent.ADMIN_QUERY:
                async for chunk in self.admin_agent.run(normalized, context):
                    yield chunk

            elif intent in (ChatIntent.ANALYTICS_REPORT, ChatIntent.LEARNING_SUMMARY):
                # Analytics agent might not be async generator yet, adapt if needed
                result = self.analytics_agent.process(context)
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        yield chunk
                else:
                    yield str(result)

            elif intent == ChatIntent.CURRICULUM_PLAN:
                # Curriculum Agent specifics
                self._enrich_curriculum_context(context, normalized)
                result = self.curriculum_agent.process(context)
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        yield chunk
                else:
                    yield str(result)

            else:
                # Fallback to pure LLM Chat
                async for chunk in self._handle_chat_fallback(normalized, context):
                    yield chunk

        except Exception as e:
            logger.error(f"Orchestrator dispatch failed: {e}", exc_info=True)
            yield "عذرًا، حدث خطأ غير متوقع أثناء معالجة طلبك."

    async def _capture_memory_intent(self, question: str, intent: ChatIntent) -> None:
        """تسجيل النية في الذاكرة بشكل صامت."""
        if not self.memory_agent:
            return
        try:
            collab_context = InMemoryCollaborationContext({"intent": intent.value})
            await self.memory_agent.capture_memory(
                collab_context,
                label="user_intent",
                payload={"question": question, "intent": intent.value}
            )
        except Exception as e:
            logger.warning(f"Memory capture failed: {e}")

    def _enrich_curriculum_context(self, context: dict, question: str) -> None:
        """إضافة تفاصيل للمسار التعليمي بناءً على نص السؤال."""
        lowered = question.lower()
        if any(x in lowered for x in ["مسار", "path", "تقدم", "progress"]):
            context["intent_type"] = "path_progress"
        elif any(x in lowered for x in ["صعب", "hard", "easy", "سهل"]):
            context["intent_type"] = "difficulty_adjust"
            context["feedback"] = "too_hard" if "صعب" in lowered else "good"
        else:
            context["intent_type"] = "recommendation"

    async def _handle_chat_fallback(self, question: str, context: dict) -> AsyncGenerator[str, None]:
        """معالجة المحادثة العامة باستخدام LLM مع السياق."""
        system_context = context.get("system_context", "")

        # Load Base Prompt
        try:
            base_prompt = get_context_service().get_admin_system_prompt()
        except Exception:
            base_prompt = "أنت مساعد ذكي."

        # Construct History
        history_msgs = context.get("history_messages", [])
        history_text = ""
        if history_msgs:
            recent = history_msgs[-10:]
            history_text = "\nSIAQ:\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent])

        final_prompt = f"{base_prompt}\n{system_context}\n{history_text}"

        messages = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": question},
        ]

        async for chunk in self.ai_client.stream_chat(messages):
            if hasattr(chunk, "choices"): # Handle different SDK response shapes
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            if content:
                yield content
