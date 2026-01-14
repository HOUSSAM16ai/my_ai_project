"""
أدوات التحليل وإعداد التقارير التعليمية.
"""

from app.core.logging import get_logger
from app.services.overmind.user_knowledge.service import UserKnowledge

logger = get_logger("reporting-tools")


async def get_student_diagnostic_report(user_id: int) -> dict[str, object]:
    """
    توليد تقرير تشخيصي شامل للطالب يغطي الأداء والتقدم ونقاط القوة.
    """
    async with UserKnowledge() as knowledge:
        profile = await knowledge.get_user_complete_profile(user_id)

    if "error" in profile:
        return profile

    # تحليل البيانات الخام لتوليد رؤى إضافية (Mock Logic here for "Superhuman" insights)
    stats = profile.get("statistics", {})
    performance = profile.get("performance", {})

    # حساب معدل الإنجاز
    total_missions = stats.get("total_missions", 0)
    completed = stats.get("completed_missions", 0)
    completion_rate = (completed / total_missions * 100) if total_missions > 0 else 0

    return {
        "user_id": user_id,
        "basic_info": profile.get("basic"),
        "metrics": {
            "completion_rate": f"{completion_rate:.1f}%",
            "active_missions": stats.get("active_missions"),
            "total_interactions": stats.get("total_chat_messages"),
        },
        "performance_indicators": performance,
        "recommendations": _generate_auto_recommendations(completion_rate),
    }

async def analyze_learning_curve(user_id: int) -> dict[str, object]:
    """
    تحليل منحنى التعلم للطالب بناءً على تاريخ النشاط.
    """
    async with UserKnowledge() as knowledge:
        stats = await knowledge.get_user_statistics(user_id)

    # Mocking a learning curve analysis based on available stats
    return {
        "learning_velocity": "High" if stats.get("total_missions", 0) > 10 else "Moderate",
        "consistency": "Stable",
        "last_active": stats.get("last_activity"),
        "trend": "Upward"
    }

def _generate_auto_recommendations(completion_rate: float) -> list[str]:
    if completion_rate > 80:
        return ["الانتقال إلى المستوى المتقدم", "تحدي مشاريع معقدة"]
    elif completion_rate > 50:
        return ["التركيز على إكمال المهام الحالية", "مراجعة المفاهيم الأساسية"]
    else:
        return ["البدء بمهام تمهيدية", "طلب مساعدة الموجه"]
