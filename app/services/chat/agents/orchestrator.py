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

            elif intent == ChatIntent.CONTENT_RETRIEVAL:
                async for chunk in self._handle_content_retrieval(normalized, context):
                    yield chunk

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

    async def _handle_content_retrieval(self, question: str, context: dict) -> AsyncGenerator[str, None]:
        """معالجة استرجاع المحتوى التعليمي (تمارين، امتحانات)."""
        logger.info(f"Handling content retrieval for: {question}")

        # 1. Extract Search Parameters (Best Effort via Heuristics or pass full query)
        # Ideally, we would use an LLM call here to extract precise JSON params,
        # but for speed and robustness, we will pass the full question as the query.
        # The tool `search_educational_content` handles semantic search.

        # Check for specific year/subject in the question to aid the tool
        year = "2024" if "2024" in question else None
        subject = None
        if any(w in question for w in ["math", "رياضيات", "رياضه"]):
            subject = "Mathematics"
        elif any(w in question for w in ["physics", "فيزياء"]):
            subject = "Physics"

        branch = None
        if any(w in question for w in ["science", "experimental", "علوم", "تجريبية", "تجريبيه"]):
            branch = "Experimental Sciences"
        elif any(w in question for w in ["math expert", "technician", "تقني", "رياضي"]):
            branch = "Mathematics"

        exam_ref = None
        if any(w in question for w in ["subject 1", "topic 1", "first subject", "موضوع 1", "موضوع الاول", "الموضوع الأول"]):
            exam_ref = "Subject 1"
        elif any(w in question for w in ["subject 2", "topic 2", "second subject", "موضوع 2", "موضوع الثاني", "الموضوع الثاني"]):
            exam_ref = "Subject 2"

        # 2. Call Retrieval Tool
        # Use execute method of ToolRegistry since it's a flat registry
        search_result = await self.tools.execute(
            "search_educational_content",
            {
                "query": question,
                "year": year,
                "subject": subject,
                "branch": branch,
                "exam_ref": exam_ref
            }
        )

        if self._is_no_content(search_result):
            # If no content is found, fallback to Smart Tutor Chat
            # This handles cases like "Explain X" which get misclassified as Content Retrieval
            async for chunk in self._handle_chat_fallback(question, context):
                yield chunk
            return

        if self._should_return_raw(search_result):
            # 1. Yield the Literal Content (Raw Transfer)
            yield search_result

            # 2. Yield Separator
            yield "\n\n---\n\n"

            # 3. Generate and Yield AI Explanation/Analysis
            personalization_context = await self._build_personalization_context(context)
            async for chunk in self._generate_explanation(
                question,
                search_result,
                personalization_context,
            ):
                yield chunk
            return

        yield self._build_strict_content_only_message()

    async def _generate_explanation(
        self,
        question: str,
        content: str,
        personalization_context: str,
    ) -> AsyncGenerator[str, None]:
        """توليد شرح أو تحليل للمحتوى المسترجع مع مراعاة ملف الطالب."""

        system_prompt = (
            "أنت مساعد تعليمي ذكي (Overmind). "
            "مهمتك هي شرح التمرين أو المحتوى الذي تم استرجاعه للطالب، أو تقديم إرشادات للحل (دون إعطاء الحل النهائي مباشرة إذا كان تمريناً للتقييم). "
            "استخدم النص المسترجع أدناه كسياق أساسي للإجابة. "
            "لا تكرر كتابة نص التمرين مرة أخرى، فقد تم عرضه بالفعل. "
            "ركز على الفهم، المفاهيم الأساسية، وطريقة التفكير. "
            "قدّم شرحاً عميقاً متعدد الطبقات يتدرّج من التعريف إلى التطبيق."
        )

        personalization_block = f"\n\n{personalization_context}" if personalization_context else ""
        user_message = f"""
سؤال الطالب: {question}

المحتوى المسترجع (تمرين/موضوع):
{content}

المطلوب: قدم شرحاً أو تلميحات مفيدة حول هذا المحتوى.
{personalization_block}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        async for chunk in self.ai_client.stream_chat(messages):
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            if content:
                yield content

    def _should_return_raw(self, search_result: str) -> bool:
        """تحديد ما إذا كان يجب إرجاع المحتوى الخام دون توليد إضافي."""
        normalized = search_result.strip()
        raw_markers = (
            "# بكالوريا",
            "## التمرين",
            "التمرين الأول",
            "التمرين الثاني",
        )
        return (
            bool(normalized)
            and any(marker in normalized for marker in raw_markers)
            and not self._is_no_content(normalized)
        )

    def _is_no_content(self, search_result: str) -> bool:
        """تحديد ما إذا كانت نتيجة البحث فارغة أو غير متوفرة."""
        normalized = search_result.strip()
        if not normalized:
            return True
        no_content_markers = (
            "لم يتم العثور على محتوى مطابق",
            "قاعدة المعرفة المحلية غير موجودة",
            "حدث خطأ أثناء استرجاع المعلومات",
            "عذرًا، حدث خطأ غير متوقع أثناء البحث",
        )
        return bool(normalized) and any(marker in normalized for marker in no_content_markers)

    def _build_strict_content_only_message(self) -> str:
        """إنشاء رسالة توضح أن الردود محصورة بمحتوى التمارين فقط."""
        lines = [
            "عذرًا، لا يمكنني تقديم إجابة عامة أو إنشاء محتوى جديد.",
            "هذا المسار يجيب فقط بنص التمارين المخزنة في قاعدة المنصة.",
            "إذا أردت تمرينًا محددًا، اطلبه بصيغة: التمرين الأول/الثاني، الموضوع الأول، سنة 2024.",
        ]
        return "\n".join(lines)

    async def _handle_chat_fallback(self, question: str, context: dict) -> AsyncGenerator[str, None]:
        """معالجة المحادثة العامة باستخدام LLM مع السياق."""
        system_context = context.get("system_context", "")

        # Load Base Prompt
        # Use Customer Prompt by default for better user alignment, or Admin if context demands.
        # Given "Overmind Education" context, Customer Prompt is safer.
        try:
            base_prompt = get_context_service().get_customer_system_prompt()
        except Exception:
            base_prompt = "أنت مساعد ذكي."

        # Strict Mode Enforcement
        # Ensure the LLM knows it is strictly bound to the educational context if present in history
        strict_instruction = (
            "\nأنت معلم ذكي ومحترف (Smart Tutor)."
            "\nسياق المحادثة (SIAQ) قد يحتوي على التمارين والدروس السابقة."
            "\nهدفك: مساعدة الطالب في فهم دروسه وتمارينه."
            "\nالقواعد:"
            "\n1. إذا توفر سياق (SIAQ)، اعتمد عليه للإجابة بدقة."
            "\n2. إذا سأل الطالب سؤالاً تعليمياً عاماً (مثل: اشرح لي الاحتمالات) ولم يوجد سياق، اشرح له المفهوم علمياً ومنهجياً بوضوح."
            "\n3. ممنوع تماماً اختراع نصوص تمارين أو امتحانات رسمية (بكالوريا) غير موجودة في السياق (Hallucination)."
            "\n4. اشرح 'لماذا' و 'كيف' (Methodology) وليس فقط النتيجة."
            "\n5. قدّم شرحاً عميقاً ومتدرجاً، مع أمثلة إن لزم."
            "\n6. كن مشجعاً، صبوراً، وتصرف كأستاذ خصوصي ممتاز."
        )

        personalization_context = await self._build_personalization_context(context)

        # Construct History
        history_msgs = context.get("history_messages", [])
        history_text = ""
        if history_msgs:
            recent = history_msgs[-10:]
            history_text = "\nSIAQ:\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent])

        personalization_block = f"\n{personalization_context}" if personalization_context else ""
        final_prompt = (
            f"{base_prompt}\n{strict_instruction}{personalization_block}\n{system_context}\n{history_text}"
        )

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

    async def _build_personalization_context(self, context: dict[str, object]) -> str:
        """بناء سياق شخصي موجز لدعم إجابة مخصصة للطالب."""
        cached_context = context.get("personalization_context")
        if isinstance(cached_context, str):
            return cached_context

        user_id = context.get("user_id")
        if not isinstance(user_id, int):
            return ""

        try:
            payload = await self.tools.execute(
                "fetch_comprehensive_student_history",
                {"user_id": user_id},
            )
        except Exception as exc:
            logger.warning("Failed to fetch student context: %s", exc)
            return ""

        if not isinstance(payload, dict):
            return ""

        stats = payload.get("profile_stats")
        missions = payload.get("missions_summary")

        profile = self._derive_learning_profile(stats, missions)
        summary_lines = self._format_profile_summary(stats, missions, profile)
        if not summary_lines:
            return ""

        personalization_context = "\n".join(summary_lines)
        context["personalization_context"] = personalization_context
        return personalization_context

    def _derive_learning_profile(
        self,
        stats: object,
        missions: object,
    ) -> dict[str, str]:
        """اشتقاق مستوى الطالب ونبرة الإرشاد المطلوبة من البيانات المتاحة."""
        level = "متوسط"
        tone = "مشجع"
        pacing = "متوازن"

        if isinstance(stats, dict):
            total_missions = stats.get("total_missions")
            completed_missions = stats.get("completed_missions")
            failed_missions = stats.get("failed_missions")
            total_messages = stats.get("total_chat_messages")

            if isinstance(total_missions, int) and total_missions <= 1:
                level = "مبتدئ"
                pacing = "بطيء مع خطوات واضحة"
            if isinstance(completed_missions, int) and isinstance(total_missions, int) and total_missions > 0:
                completion_ratio = completed_missions / total_missions
                if completion_ratio >= 0.75:
                    level = "متقدم"
                    pacing = "سريع مع تحديات إضافية"
            if isinstance(failed_missions, int) and failed_missions >= 2:
                tone = "داعِم مع إعادة تبسيط"
                pacing = "متدرج مع أمثلة إضافية"
            if isinstance(total_messages, int) and total_messages < 5:
                tone = "ترحيبي وهادئ"

        focus = "الربط بين الفكرة والخطوات العملية"
        if isinstance(missions, dict):
            topics = missions.get("topics")
            if isinstance(topics, list):
                topic_list = [topic for topic in topics if isinstance(topic, str)]
                if topic_list:
                    focus = f"ربط الشرح بمواضيع الطالب الحديثة مثل: {', '.join(topic_list[:3])}"

        return {
            "level": level,
            "tone": tone,
            "pacing": pacing,
            "focus": focus,
        }

    def _format_profile_summary(
        self,
        stats: object,
        missions: object,
        profile: dict[str, str],
    ) -> list[str]:
        """صياغة ملخص شخصي قابل للإدراج داخل تعليمات الوكيل."""
        lines: list[str] = ["ملف الطالب المختصر (للتخصيص فقط):"]
        lines.append(f"- مستوى تقريبي: {profile['level']}")
        lines.append(f"- أسلوب الشرح: {profile['tone']}، بإيقاع {profile['pacing']}")
        lines.append(f"- محور التركيز: {profile['focus']}")

        if isinstance(stats, dict):
            total_missions = stats.get("total_missions")
            completed_missions = stats.get("completed_missions")
            failed_missions = stats.get("failed_missions")
            total_messages = stats.get("total_chat_messages")
            last_activity = stats.get("last_activity")
            if isinstance(total_missions, int):
                lines.append(f"- إجمالي المهام: {total_missions}")
            if isinstance(completed_missions, int):
                lines.append(f"- المهام المكتملة: {completed_missions}")
            if isinstance(failed_missions, int):
                lines.append(f"- المهام غير المكتملة: {failed_missions}")
            if isinstance(total_messages, int):
                lines.append(f"- إجمالي رسائل التعلم: {total_messages}")
            if isinstance(last_activity, str) and last_activity:
                lines.append(f"- آخر نشاط: {last_activity}")

        if isinstance(missions, dict):
            topics = missions.get("topics")
            recent = missions.get("recent_missions")
            if isinstance(topics, list):
                topic_list = [topic for topic in topics if isinstance(topic, str)]
                if topic_list:
                    lines.append(f"- مواضيع حديثة: {', '.join(topic_list[:6])}")
            if isinstance(recent, list) and recent:
                latest = recent[0]
                if isinstance(latest, dict):
                    title = latest.get("title")
                    status = latest.get("status")
                    if isinstance(title, str) and isinstance(status, str):
                        lines.append(f"- آخر مهمة: {title} ({status})")

        return lines if len(lines) > 1 else []
