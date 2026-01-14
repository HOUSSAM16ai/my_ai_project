"""
وكيل تحليل الأداء (Analytics Agent) - النسخة الخارقة (Superhuman Edition).

يستخدم الذكاء الاصطناعي لتحليل سجلات الدردشة والمهام بدقة متناهية.
"""

from typing import AsyncGenerator

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.tools import ToolRegistry

logger = get_logger("analytics-agent")


class AnalyticsAgent:
    """
    وكيل متخصص في تحليل بيانات الطلاب التعليمية وتقديم تقارير تشخيصية "عبقرية".
    """

    def __init__(self, tools: ToolRegistry, ai_client: AIClient | None = None) -> None:
        self.tools = tools
        self.ai_client = ai_client

    async def process(self, context: dict[str, object]) -> AsyncGenerator[str, None]:
        """
        تنفيذ عملية التحليل العميق باستخدام AI Client مباشرة.
        """
        logger.info("Analytics agent started processing (Superhuman Mode)")

        user_id = context.get("user_id")
        if not user_id:
            yield "عذراً، لم أتمكن من تحديد هوية المستخدم لتحليل بياناته."
            return

        if not self.ai_client:
            yield "⚠️ خطأ داخلي: لم يتم تزويد الوكيل بمحرك الذكاء الاصطناعي."
            return

        yield "🔍 **جاري استدعاء سجلاتك الدراسية وتحليل محادثاتك السابقة بالكامل...**\n"

        # 1. Fetch Comprehensive Data (Chat Logs + Missions)
        try:
            data = await self.tools.execute("fetch_comprehensive_student_history", {"user_id": user_id})
        except Exception as e:
            logger.error(f"Error fetching comprehensive history: {e}")
            yield "حدث خطأ أثناء جلب البيانات."
            return

        # 2. Construct the Superhuman Prompt
        chat_logs = data.get("chat_history_text", "No logs.")
        missions = data.get("missions_summary", {})
        stats = data.get("profile_stats", {})

        system_prompt = (
            "You are a Superhuman Educational Analyst and Mentor (المرشد الأكاديمي العبقري).\n"
            "Your goal is to analyze the student's *entire* interaction history to provide a deep, psychological, and academic diagnosis.\n"
            "DO NOT just list stats. Analyze the *content* of their questions.\n\n"
            "Data Provided:\n"
            f"1. **Chat Logs (Last ~60 messages):**\n{chat_logs}\n\n"
            f"2. **Mission History:**\n{missions}\n\n"
            f"3. **Stats:**\n{stats}\n\n"
            "**Output Requirements:**\n"
            "- Tone: Professional, Encouraging, Highly Insightful (Arabic).\n"
            "- **Cognitive Analysis:** How does the student think? Are they confused by syntax or logic? Do they ask deep questions?\n"
            "- **Curriculum Alignment:** Where do they stand vs a standard roadmap?\n"
            "- **Weaknesses:** Specific concepts they struggled with in the chat.\n"
            "- **Actionable Plan:** 3 specific, non-generic steps.\n"
            "- Format with Markdown headers, bullet points, and emojis."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "حلل أدائي الدراسي بناءً على كل ما تعرفه عني."}
        ]

        # 3. Stream the AI Analysis
        yield "\n" # Spacing

        try:
            async for chunk in self.ai_client.stream_chat(messages):
                # Extract content depending on client wrapper structure
                content = ""
                if isinstance(chunk, dict):
                    # OpenAI-like format
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                elif hasattr(chunk, "choices"):
                     # Object format
                     if chunk.choices:
                         content = chunk.choices[0].delta.content or ""

                if content:
                    yield content

        except Exception as exc:
            logger.error(f"AI Analysis Failed: {exc}")
            yield "\n⚠️ حدث خطأ أثناء توليد التحليل الذكي. يرجى المحاولة لاحقاً."
