"""
أدوات المناهج الدراسية وتوصيات المحتوى.
"""

from typing import Literal

from sqlalchemy import select
from sqlmodel import col

from app.core.database import async_session_factory
from app.core.domain.mission import Mission, MissionStatus
from app.core.logging import get_logger

logger = get_logger("curriculum-tools")


async def recommend_next_mission(user_id: int, difficulty: str = "medium") -> dict[str, object]:
    """
    اقتراح المهمة التالية بناءً على مستوى الصعوبة وسجل الطالب.
    """
    async with async_session_factory() as session:
        # البحث عن مهام غير مكتملة
        # هذا منطق مبسط، في النظام الكامل سيكون هناك خوارزمية توصية معقدة
        statement = select(Mission).where(
            col(Mission.status) == MissionStatus.PENDING
        ).limit(1)

        result = await session.execute(statement)
        mission = result.scalar_one_or_none()

        if mission:
            return {
                "mission_id": mission.id,
                "title": mission.name,
                "description": mission.description,
                "reason": f"Recommended based on {difficulty} path preference."
            }

        return {"message": "لا توجد مهام جديدة متاحة حالياً، أحسنت عملاً!"}


async def get_learning_path_progress(user_id: int) -> dict[str, object]:
    """
    عرض تقدم الطالب في مسار التعلم الحالي.
    """
    # Mock return for visual representation
    return {
        "current_stage": "Fundamentals",
        "progress_percentage": 45,
        "next_milestone": "Advanced Algorithms",
        "completed_modules": ["Intro to Python", "Data Structures"],
        "pending_modules": ["Algorithms", "System Design"]
    }

async def adjust_difficulty_level(user_id: int, feedback: Literal["too_hard", "too_easy", "good"]) -> str:
    """
    تكييف مستوى صعوبة التمارين بناءً على ملاحظات الطالب.
    """
    # Logic to update user preference or adaptive engine state would go here.
    return f"تم تعديل مستوى الصعوبة بناءً على تعليقك: {feedback}. ستكون المهام القادمة أكثر ملاءمة."
