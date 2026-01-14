"""
وكيل المناهج (Curriculum Agent).

مسؤول عن:
1. اقتراح مسارات تعلم مخصصة.
2. تعديل مستوى الصعوبة (Adaptive Learning).
3. اختيار التمارين المناسبة للمستوى الحالي.
"""

from typing import AsyncGenerator

from app.core.logging import get_logger
from app.services.chat.tools import ToolRegistry

logger = get_logger("curriculum-agent")


class CurriculumAgent:
    """
    وكيل "المصمم التعليمي" المسؤول عن توجيه رحلة التعلم واختيار المحتوى.
    """

    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools

    async def process(self, context: dict[str, object]) -> AsyncGenerator[str, None]:
        """
        معالجة طلبات المحتوى والتمارين.
        """
        logger.info("Curriculum agent started processing")

        intent_type = context.get("intent_type", "recommendation")
        user_id = context.get("user_id")

        if not user_id:
            yield "عذراً، أحتاج لمعرفة هويتك لتقديم توصيات مناسبة."
            return

        if intent_type == "path_progress":
            yield await self._handle_path_progress(user_id)
        elif intent_type == "difficulty_adjust":
             yield await self._handle_difficulty_adjustment(user_id, context.get("feedback", "good"))
        else:
            async for chunk in self._handle_recommendation(user_id):
                yield chunk

    async def _handle_recommendation(self, user_id: int) -> AsyncGenerator[str, None]:
        yield "جاري البحث عن أنسب تمرين لمستواك الحالي... 🎯\n"

        try:
            mission = await self.tools.execute("recommend_next_mission", {"user_id": user_id})
        except Exception as e:
            logger.error(f"Error recommending mission: {e}")
            yield "حدث خطأ أثناء البحث عن مهام."
            return

        if "message" in mission:
            yield mission["message"]
            return

        yield (
            f"### 🚀 المهمة المقترحة: {mission.get('title')}\n\n"
            f"{mission.get('description')}\n\n"
            f"**لماذا اخترنا هذا لك؟**\n{mission.get('reason')}"
        )

    async def _handle_path_progress(self, user_id: int) -> str:
        try:
            progress = await self.tools.execute("get_learning_path_progress", {"user_id": user_id})
        except Exception as e:
            logger.error(f"Error fetching progress: {e}")
            return "تعذر جلب بيانات المسار."

        return (
            f"## 🗺️ مسار التعلم الخاص بك\n"
            f"- **المرحلة الحالية:** {progress.get('current_stage')}\n"
            f"- **نسبة الإنجاز:** {progress.get('progress_percentage')}%\n"
            f"- **المحطة القادمة:** {progress.get('next_milestone')}"
        )

    async def _handle_difficulty_adjustment(self, user_id: int, feedback: str) -> str:
        try:
             result = await self.tools.execute("adjust_difficulty_level", {"user_id": user_id, "feedback": feedback})
             return f"✅ {result}"
        except Exception as e:
             logger.error(f"Error adjusting difficulty: {e}")
             return "حدث خطأ أثناء تعديل الإعدادات."
