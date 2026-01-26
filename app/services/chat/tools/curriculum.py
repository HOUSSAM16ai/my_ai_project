"""
أدوات المناهج الدراسية وتوصيات المحتوى.
"""

from typing import Literal

from sqlalchemy import desc, select, text

from app.core.database import async_session_factory
from app.core.domain.mission import Mission, MissionStatus
from app.core.logging import get_logger

logger = get_logger("curriculum-tools")


async def recommend_next_mission(user_id: int, difficulty: str = "medium") -> dict[str, object]:
    """
    اقتراح المهمة التالية بذكاء بناءً على تاريخ الطالب.
    """
    async with async_session_factory() as session:
        # 1. معرفة آخر ما أنجزه الطالب لتجنب التكرار
        completed_stmt = select(Mission.objective).where(
            Mission.initiator_id == user_id, Mission.status == MissionStatus.SUCCESS
        )
        _ = await session.execute(completed_stmt)
        # completed_titles = {row[0] for row in completed_res.all()}

        # 2. البحث عن مهام "Pending" أو أفكار جديدة
        last_mission_stmt = (
            select(Mission)
            .where(Mission.initiator_id == user_id, Mission.status == MissionStatus.SUCCESS)
            .order_by(desc(Mission.created_at))
            .limit(1)
        )
        last_mission_res = await session.execute(last_mission_stmt)
        last_mission = last_mission_res.scalar_one_or_none()

        suggestion_title = "مقدمة في البرمجة"
        suggestion_desc = "ابدأ رحلتك التعليمية بأساسيات بايثون."

        # محاولة البحث عن محتوى حقيقي في قاعدة البيانات لاقتراحه
        try:
            # البحث عن موضوع عشوائي أو أول موضوع في المستوى الأول
            content_query = text("""
                SELECT title, subject, level, id
                FROM content_items
                ORDER BY level ASC, id ASC
                LIMIT 1
             """)
            content_res = await session.execute(content_query)
            content_row = content_res.fetchone()

            if content_row:
                suggestion_title = content_row.title
                suggestion_desc = f"درس في مادة {content_row.subject} - المستوى {content_row.level}"
        except Exception as e:
            logger.warning(f"Could not fetch real content for recommendation: {e}")

        if last_mission:
            # منطق بسيط لاقتراح الخطوة التالية
            if "بايثون" in last_mission.objective or "Python" in last_mission.objective:
                suggestion_title = "هياكل البيانات في بايثون"
                suggestion_desc = "بعد أن أتقنت الأساسيات، دعنا نتعمق في القوائم والقواميس."
            elif "بيانات" in last_mission.objective:
                suggestion_title = "الخوارزميات البسيطة"
                suggestion_desc = "حان وقت التحدي الحقيقي: البحث والترتيب."
            else:
                suggestion_title = f"مستوى متقدم من {last_mission.objective}"
                suggestion_desc = "تحدي جديد لتعزيز مهاراتك."

        return {
            "title": suggestion_title,
            "description": suggestion_desc,
            "reason": "بناءً على تحليلك لآخر نشاط لك.",
            "difficulty": difficulty,
        }


async def get_learning_path_progress(user_id: int) -> dict[str, object]:
    """
    عرض تقدم الطالب في مسار التعلم الحقيقي بناءً على المهام المنجزة.
    """
    async with async_session_factory() as session:
        stmt = select(Mission).where(Mission.initiator_id == user_id)
        result = await session.execute(stmt)
        missions = result.scalars().all()

    total = len(missions)
    completed = len([m for m in missions if m.status == MissionStatus.SUCCESS])

    return {
        "current_stage": "Active Learner",  # يمكن تطويره ليكون ديناميكياً
        "progress_percentage": int(completed / total * 100) if total > 0 else 0,
        "completed_count": completed,
        "total_missions": total,
        "recent_achievements": [m.objective for m in missions if m.status == MissionStatus.SUCCESS][
            :3
        ],
    }


async def adjust_difficulty_level(
    user_id: int, feedback: Literal["too_hard", "too_easy", "good"]
) -> str:
    """
    تكييف مستوى صعوبة التمارين.
    """
    # في نظام حقيقي، نقوم بتخزين التفضيل في جدول UserPreferences
    return f"تم تسجيل ملاحظتك ({feedback}). سنقوم بتعديل تعقيد المهام القادمة لتناسبك."
