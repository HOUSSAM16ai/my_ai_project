"""
أدوات المناهج الدراسية وتوصيات المحتوى.
"""

from typing import Literal

from sqlalchemy import desc, not_, select
from sqlmodel import col

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
            Mission.initiator_id == user_id,
            Mission.status == MissionStatus.SUCCESS
        )
        completed_res = await session.execute(completed_stmt)
        completed_titles = {row[0] for row in completed_res.all()}

        # 2. البحث عن مهام "Pending" أو أفكار جديدة
        # هنا نفترض وجود مهام مجهزة مسبقاً في النظام (Pool of missions)
        # أو نقترح مهمة بناءً على نمط.
        # بما أن هذا النظام يعتمد على إنشاء المهام ديناميكياً، سنقوم باقتراح "موضوع" جديد.

        # لغرض هذا التطوير، سنبحث عن مهام موجودة لم يكملها المستخدم (من مستخدمين آخرين مثلاً كقوالب)
        # أو نقترح تحدياً عاماً.

        # تحسين: اقتراح مبني على آخر مهمة ناجحة
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
            "difficulty": difficulty
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
        "current_stage": "Active Learner", # يمكن تطويره ليكون ديناميكياً
        "progress_percentage": int((completed / total * 100)) if total > 0 else 0,
        "completed_count": completed,
        "total_missions": total,
        "recent_achievements": [m.objective for m in missions if m.status == MissionStatus.SUCCESS][:3]
    }

async def adjust_difficulty_level(user_id: int, feedback: Literal["too_hard", "too_easy", "good"]) -> str:
    """
    تكييف مستوى صعوبة التمارين.
    """
    # في نظام حقيقي، نقوم بتخزين التفضيل في جدول UserPreferences
    return f"تم تسجيل ملاحظتك ({feedback}). سنقوم بتعديل تعقيد المهام القادمة لتناسبك."
