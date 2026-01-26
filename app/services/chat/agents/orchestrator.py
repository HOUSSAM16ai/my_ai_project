import json
import logging
from collections.abc import AsyncGenerator

from app.core.ai_gateway import AIClient
from app.services.chat.agents.admin import AdminAgent
from app.services.chat.agents.analytics import AnalyticsAgent
from app.services.chat.agents.curriculum import CurriculumAgent
from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.education_council import EducationCouncil
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.context_service import get_context_service
from app.services.chat.intent_detector import ChatIntent, IntentDetector
from app.services.chat.tools import ToolRegistry
from app.services.overmind.agents.memory import MemoryAgent
from app.services.overmind.domain.context import InMemoryCollaborationContext

logger = logging.getLogger("orchestrator-agent")


class OrchestratorRunResult:
    """
    نتيجة تشغيل وكيل التنسيق.

    تدعم البث عبر التكرار غير المتزامن، كما تسمح بانتظار النتيجة كنص كامل.
    """

    def __init__(self, stream: AsyncGenerator[str, None]) -> None:
        self._stream = stream

    def __aiter__(self) -> AsyncGenerator[str, None]:
        return self._stream

    def __await__(self):
        async def _collect() -> str:
            chunks: list[str] = []
            async for chunk in self._stream:
                chunks.append(chunk)
            return "".join(chunks)

        return _collect().__await__()


class OrchestratorAgent:
    """
    الوكيل المنسق (Orchestrator Agent).

    يعمل كنقطة دخول مركزية لتوجيه الطلبات إلى الوكلاء المتخصصين.
    يدعم استرجاع المحتوى الدقيق باستخدام الأدوات الجديدة والبحث الدلالي.
    """

    def __init__(self, ai_client: AIClient, tools: ToolRegistry) -> None:
        self.ai_client = ai_client
        self.tools = tools
        self.intent_detector = IntentDetector()

        # Sub-Agents
        self.admin_agent = AdminAgent(tools, ai_client=ai_client)
        self.analytics_agent = AnalyticsAgent(tools, ai_client)
        self.curriculum_agent = CurriculumAgent(tools)
        self.memory_agent = MemoryAgent()
        self.education_council = EducationCouncil(tools)

    @property
    def data_agent(self) -> DataAccessAgent:
        """إتاحة وكيل البيانات للوصول والاختبار."""
        return self.admin_agent.data_agent

    @data_agent.setter
    def data_agent(self, value: DataAccessAgent) -> None:
        self.admin_agent.data_agent = value

    @property
    def refactor_agent(self) -> RefactorAgent:
        """إتاحة وكيل التحسينات للوصول والاختبار."""
        return self.admin_agent.refactor_agent

    @refactor_agent.setter
    def refactor_agent(self, value: RefactorAgent) -> None:
        self.admin_agent.refactor_agent = value

    def run(self, question: str, context: dict[str, object] | None = None) -> OrchestratorRunResult:
        """
        واجهة موحدة لمعالجة الطلبات مع دعم البث أو التجميع النصي.
        """
        return OrchestratorRunResult(self._run_stream(question, context))

    async def _run_stream(
        self,
        question: str,
        context: dict[str, object] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        التنفيذ الفعلي لمسار البث.
        """
        logger.info(f"Orchestrator received: {question}")
        normalized = question.strip()
        context = context or {}

        # 1. Intent Detection
        if "intent" in context and isinstance(context["intent"], ChatIntent):
            intent = context["intent"]
        else:
            intent_result = await self.intent_detector.detect(normalized)
            intent = intent_result.intent

        # 2. Memory Capture (Best Effort)
        await self._capture_memory_intent(normalized, intent)

        # 3. Dispatch
        try:
            if intent in {ChatIntent.ADMIN_QUERY, ChatIntent.CODE_SEARCH, ChatIntent.PROJECT_INDEX}:
                async for chunk in self.admin_agent.run(normalized, context):
                    yield chunk

            elif intent in (ChatIntent.ANALYTICS_REPORT, ChatIntent.LEARNING_SUMMARY):
                result = self.analytics_agent.process(context)
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        yield chunk
                else:
                    yield str(result)

            elif intent == ChatIntent.CURRICULUM_PLAN:
                self._enrich_curriculum_context(context, normalized)
                context["user_message"] = normalized
                result = self.curriculum_agent.process(context)
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        yield chunk
                else:
                    yield str(result)

            elif intent == ChatIntent.CONTENT_RETRIEVAL:
                async for chunk in self._handle_content_retrieval(normalized, context):
                    yield chunk

            else:
                async for chunk in self._handle_chat_fallback(normalized, context):
                    yield chunk

        except Exception as e:
            logger.error(f"Orchestrator dispatch failed: {e}", exc_info=True)
            yield "عذرًا، حدث خطأ غير متوقع أثناء معالجة طلبك."

    async def _capture_memory_intent(self, question: str, intent: ChatIntent) -> None:
        if not self.memory_agent:
            return
        try:
            collab_context = InMemoryCollaborationContext({"intent": intent.value})
            await self.memory_agent.capture_memory(
                collab_context,
                label="user_intent",
                payload={"question": question, "intent": intent.value},
            )
        except Exception as e:
            logger.warning(f"Memory capture failed: {e}")

    def _enrich_curriculum_context(self, context: dict, question: str) -> None:
        lowered = question.lower()
        if any(x in lowered for x in ["مسار", "path", "تقدم", "progress"]):
            context["intent_type"] = "path_progress"
        elif any(x in lowered for x in ["صعب", "hard", "easy", "سهل"]):
            context["intent_type"] = "difficulty_adjust"
            context["feedback"] = "too_hard" if "صعب" in lowered else "good"
        else:
            context["intent_type"] = "recommendation"

    async def _handle_content_retrieval(
        self, question: str, context: dict
    ) -> AsyncGenerator[str, None]:
        """
        معالجة استرجاع المحتوى:
        1. استخراج الفلاتر بذكاء (AI Extraction) من النص الطبيعي.
        2. البحث عن IDs باستخدام search_content (الذي يدعم الآن الكلمات المتعددة).
        3. جلب المحتوى الخام وعرضه.
        4. توليد الشرح.
        """
        logger.info(f"Handling content retrieval for: {question}")

        # Step 1: Intelligent Search Parameter Extraction using LLM
        params = await self._ai_extract_search_params(question)

        candidates = await self.tools.execute("search_content", params)

        if not candidates:
            logger.info("No content found for query, falling back to smart tutor.")
            # Inject a hint into context so fallback knows we missed a search
            context["search_miss"] = True
            async for chunk in self._handle_chat_fallback(question, context):
                yield chunk
            return

        # Pick the best candidate (Logic: Top 1)
        best_candidate = candidates[0]
        content_id = best_candidate["id"]
        title = best_candidate["title"]

        yield f"✅ **تم العثور على:** {title} ({content_id})\n\n"

        # Step 2: Fetch Raw Content
        raw_data = await self.tools.execute("get_content_raw", {"content_id": content_id})

        if raw_data and raw_data.get("content"):
            yield "---\n\n"
            yield raw_data["content"]
            yield "\n\n---\n\n"

            # Step 3: AI Explanation with Official Solution
            personalization_context = await self._build_education_brief(context)
            solution = raw_data.get("solution")

            async for chunk in self._generate_explanation(
                question, raw_data["content"], personalization_context, solution=solution
            ):
                yield chunk
        else:
            yield "عذراً، تعذر تحميل نص المحتوى."

    async def _ai_extract_search_params(self, question: str) -> dict:
        """
        Uses LLM to extract structured search parameters from natural language.
        Fallback to heuristics if LLM fails.
        """
        system_prompt = (
            "You are a search query parser for an educational database. "
            "Extract parameters from the user's request into a JSON object. "
            "Fields: q (keywords), year (int), subject (Mathematics, Physics), branch (experimental_sciences, math_tech, etc), set_name, level, type (exercise, lesson). "
            "\nRules:"
            "\n1. 'Subject 1' -> set_name: 'subject_1', 'Subject 2' -> set_name: 'subject_2'."
            "\n2. 'Experimental Sciences' (علوم تجريبية) -> branch: 'experimental_sciences'."
            "\n3. 'Math Tech' (تقني رياضي) -> branch: 'math_tech'."
            "\n4. 'Mathematics' or 'Math' -> subject: 'Mathematics'."
            "\n5. 'Baccalaureate' or 'Bac' -> level: 'baccalaureate'."
            "\n6. If a field is not present, omit it."
            "\n\nExample 1: 'Math exercises 2024 probability' -> {'q': 'probability', 'year': 2024, 'subject': 'Mathematics'}"
            "\nExample 2: 'Subject 1 Bac 2024 Experimental Probability' -> {'q': 'Probability', 'year': 2024, 'set_name': 'subject_1', 'branch': 'experimental_sciences', 'level': 'baccalaureate'}"
        )

        try:
            # Quick parsing call
            response = await self.ai_client.generate(
                model="gpt-4o-mini",  # Use a fast model if available, or default
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            params = json.loads(content)

            # Ensure limit default
            params["limit"] = 5

            # Fallback for 'q' if empty, use original question
            if not params.get("q") and not params.get("year"):
                params["q"] = question

            return params

        except Exception as e:
            logger.warning(f"AI parameter extraction failed: {e}. using heuristics.")
            return self._heuristic_extract_search_params(question)

    def _heuristic_extract_search_params(self, question: str) -> dict:
        """Fallback heuristic parameter extraction."""
        params = {"q": question, "limit": 5}

        if "2024" in question:
            params["year"] = 2024

        if any(w in question for w in ["math", "رياضيات", "رياضه"]):
            params["subject"] = "Mathematics"
        elif any(w in question for w in ["physics", "فيزياء"]):
            params["subject"] = "Physics"

        return params

    async def _generate_explanation(
        self, question: str, content: str, personalization_context: str, solution: str | None = None
    ) -> AsyncGenerator[str, None]:
        """
        توليد شرح أو تحليل للمحتوى المسترجع.
        يستخدم 'الحل الرسمي' (Official Solution) كمرجع أساسي (Source of Truth) إذا توفر.
        """

        # بناء التعليمات الأساسية (System Prompt)
        # نركز على كون الوكيل "Smart Tutor" يشرح بعمق ويبسط المعلومة بناءً على الحل الرسمي.

        system_prompt = (
            "أنت 'Overmind'، المعلم الذكي فائق القدرات (Smart Tutor)."
            "\nمهمتك: تقديم شرح فاخر (Luxury)، عميق، ومبسط للتمرين المسترجع."
            "\n\nالتعليمات الصارمة:"
            "\n1. التزم كلياً بـ 'الحل الرسمي' (Official Solution) الموجود في السياق أدناه. هو المصدر الوحيد للحقيقة."
            "\n2. لا تكتفِ بسرد الحل؛ اشرح 'لماذا' و 'كيف' وصلنا لهذه النتيجة."
            "\n3. بسّط المفاهيم المعقدة لتناسب طالباً ذا قدرات محدودة، لكن بأسلوب راقٍ واحترافي."
            "\n4. إذا لم يوجد حل رسمي، استخدم خبرتك لشرح المفهوم دون اختراع أرقام."
            "\n5. الهدف: جعل الطالب يفهم أعمق التفاصيل بسهولة تامة."
        )

        if personalization_context:
            system_prompt += f"\n\nمرجع الجودة التعليمية الموحد:\n{personalization_context}"

        # بناء رسالة المستخدم (Context Injection)
        user_message = f"سؤال الطالب: {question}\n\n"
        user_message += f"نص التمرين (Exercise):\n{content}\n\n"

        if solution:
            user_message += (
                f"الحل الرسمي (Official Solution - STRICTLY ADHERE TO THIS):\n{solution}\n\n"
            )
        else:
            user_message += "ملاحظة: لا يوجد حل رسمي مسجل. اشرح المفهوم العام فقط.\n\n"

        user_message += "المطلوب: اشرح الحل للطالب بأسلوب 'Smart Tutor' (عميق، مبسط، واحترافي)."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        async for chunk in self._stream_ai_chunks(messages):
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            if content:
                yield content

    async def _handle_chat_fallback(
        self, question: str, context: dict
    ) -> AsyncGenerator[str, None]:
        """معالجة المحادثة العامة."""
        system_context = context.get("system_context", "")

        try:
            base_prompt = get_context_service().get_customer_system_prompt()
        except Exception:
            base_prompt = "أنت مساعد ذكي."

        # SMART TUTOR LOGIC
        # We permit general explanation if no specific exercise is loaded,
        # but strictly forbid fabricating specific numbers/exercises.
        strict_instruction = (
            "\nأنت معلم ذكي ومحترف (Smart Tutor)."
            "\nالقواعد الصارمة:"
            "\n1. إذا توفر محتوى تمرين في السياق (SIAQ)، التزم به حرفياً."
            "\n2. إذا لم يتوفر تمرين، اشرح المفهوم العلمي/الرياضي بشكل عام (General Concept) وشامل."
            "\n3. ممنوع منعاً باتاً اختراع تمارين أو أرقام من خيالك. قل 'لا يوجد تمرين محدد، لكن الفكرة هي...'."
            "\n4. اشرح 'لماذا' و 'كيف' دائماً لتبسيط التعقيدات."
        )

        personalization_context = await self._build_education_brief(context)

        # History
        history_msgs = context.get("history_messages", [])
        history_text = ""
        if history_msgs:
            recent = history_msgs[-10:]
            history_text = "\nSIAQ (History):\n" + "\n".join(
                [f"{m.get('role')}: {m.get('content')}" for m in recent]
            )

        personalization_block = ""
        if personalization_context:
            personalization_block = f"\nمرجع الجودة:\n{personalization_context}"
        final_prompt = f"{base_prompt}\n{strict_instruction}{personalization_block}\n{system_context}\n{history_text}"

        messages = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": question},
        ]

        async for chunk in self._stream_ai_chunks(messages):
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            if content:
                yield content

    async def _build_education_brief(self, context: dict[str, object]) -> str:
        """بناء موجز تعليمي."""
        cached_context = context.get("education_brief")
        if isinstance(cached_context, str):
            return cached_context

        try:
            brief = await self.education_council.build_brief(context=context)
        except Exception as exc:
            logger.warning("Failed to build education brief: %s", exc)
            return ""

        rendered = brief.render()
        context["education_brief"] = rendered
        return rendered

    async def _stream_ai_chunks(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[object, None]:
        """
        بث استجابات النموذج مع دعم نتائج قابلة للانتظار من AsyncMock.
        """
        if not self.ai_client:
            raise RuntimeError("عميل الذكاء الاصطناعي غير متوفر.")
        stream_result = self.ai_client.stream_chat(messages)
        if hasattr(stream_result, "__await__"):
            stream_result = await stream_result  # type: ignore[assignment]
        async for chunk in stream_result:
            yield chunk
