"""
أدوات التحليل وإعداد التقارير التعليمية.
"""

from typing import cast

from sqlalchemy import desc, func, select

from app.core.database import async_session_factory
from app.core.domain.mission import Mission, MissionStatus, Task, TaskStatus
from app.core.logging import get_logger
from app.services.overmind.user_knowledge.service import UserKnowledge

logger = get_logger("reporting-tools")


async def get_student_diagnostic_report(user_id: int) -> dict[str, object]:
    """
    توليد تقرير تشخيصي شامل للطالب يغطي الأداء والتقدم ونقاط القوة،
    معتمد على بيانات حقيقية من المهام (Missions).
    """
    async with UserKnowledge() as knowledge:
        profile = await knowledge.get_user_complete_profile(user_id)

    if "error" in profile:
        return profile

    # جلب تفاصيل المهام الحقيقية
    missions_summary = await _get_detailed_missions_summary(user_id)

    # دمج البيانات
    stats = profile.get("statistics", {})
    performance = profile.get("performance", {})

    return {
        "user_id": user_id,
        "basic_info": profile.get("basic"),
        "metrics": {
            "completion_rate": _calculate_completion_rate(stats),
            "total_missions": stats.get("total_missions", 0),
            "completed_missions": stats.get("completed_missions", 0),
            "total_interactions": stats.get("total_chat_messages"),
        },
        "recent_activity": missions_summary["recent_missions"],
        "topics_covered": missions_summary["topics"],  # استنتاج المواضيع من عناوين المهام
        "performance_indicators": performance,
        "recommendations": _generate_smart_recommendations(missions_summary),
    }

async def analyze_learning_curve(user_id: int) -> dict[str, object]:
    """
    تحليل منحنى التعلم للطالب بناءً على تواريخ إنجاز المهام.
    """
    async with async_session_factory() as session:
        # جلب تواريخ المهام المكتملة
        stmt = (
            select(Mission.updated_at, Mission.objective)
            .where(Mission.initiator_id == user_id, Mission.status == MissionStatus.SUCCESS)
            .order_by(Mission.updated_at)
        )
        result = await session.execute(stmt)
        history = result.all()

    if not history:
        return {"status": "no_data", "message": "لا توجد بيانات كافية لتحليل المنحنى."}

    # تحليل بسيط للسرعة (عدد المهام في الأسبوع)
    # يمكن تطويره ليكون أكثر تعقيداً
    return {
        "total_completed": len(history),
        "last_achievement": history[-1].objective if history else None,
        "last_active_date": history[-1].updated_at.isoformat() if history else None,
        "consistency_score": "High" if len(history) > 5 else "Growing",
        "trend": "Active Learner"
    }

async def _get_detailed_missions_summary(user_id: int) -> dict[str, object]:
    """
    جلب ملخص تفصيلي عن آخر المهام.
    """
    async with async_session_factory() as session:
        stmt = (
            select(Mission)
            .where(Mission.initiator_id == user_id)
            .order_by(desc(Mission.created_at))
            .limit(5)
        )
        result = await session.execute(stmt)
        missions = result.scalars().all()

    recent = []
    topics = set()

    for m in missions:
        recent.append({
            "id": m.id,
            "title": m.objective[:50] + "..." if len(m.objective) > 50 else m.objective,
            "status": m.status.value,
            "date": m.created_at.isoformat(),
        })
        # استخراج كلمات مفتاحية بسيطة كـ "مواضيع"
        # في نظام حقيقي، نستخدم NLP أو Tags
        words = m.objective.split()
        if len(words) > 0:
            topics.add(words[0]) # مجرد مثال

    return {
        "recent_missions": recent,
        "topics": list(topics)
    }

def _calculate_completion_rate(stats: dict) -> str:
    total = stats.get("total_missions", 0)
    completed = stats.get("completed_missions", 0)
    if total == 0:
        return "N/A"
    return f"{(completed / total * 100):.1f}%"

def _generate_smart_recommendations(summary: dict) -> list[str]:
    recent = summary.get("recent_missions", [])
    if not recent:
        return ["ابدأ أول مهمة لك اليوم!"]

    failed_missions = [m for m in recent if m["status"] == "failed"]
    if failed_missions:
        return [f"مراجعة أسباب فشل المهمة: {failed_missions[0]['title']}"]

    return ["استمر في التقدم، أداؤك جيد!"]
