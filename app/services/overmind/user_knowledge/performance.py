"""
إدارة مقاييس أداء المستخدمين (User Performance Metrics Management).

يوفر مقاييس الأداء والإنتاجية للمستخدمين.

المبادئ:
- Single Responsibility: فقط مقاييس الأداء
- Analytics: تحليلات متقدمة
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.core.domain.models import Mission
from app.services.overmind.user_knowledge.statistics import get_user_statistics

logger = get_logger(__name__)


async def get_user_performance(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    الحصول على مقاييس أداء المستخدم.
    
    Args:
        session: جلسة قاعدة البيانات
        user_id: معرّف المستخدم
        
    Returns:
        dict: مقاييس الأداء
        
    يشمل:
        - success_rate: معدل النجاح (%)
        - average_mission_duration_hours: متوسط مدة المهمة (ساعات)
        - missions_per_week: المهام في الأسبوع
        - productivity_score: درجة الإنتاجية (0-100)
        - quality_score: درجة الجودة (0-100)
    """
    try:
        performance = {}
        
        # معدل النجاح (Success Rate)
        stats = await get_user_statistics(session, user_id)
        total = stats.get("total_missions", 0)
        completed = stats.get("completed_missions", 0)
        
        if total > 0:
            performance["success_rate"] = (completed / total) * 100
        else:
            performance["success_rate"] = 0.0
        
        # متوسط مدة المهمة (Average Mission Duration)
        duration_query = select(
            func.avg(
                func.extract('epoch', Mission.updated_at) - 
                func.extract('epoch', Mission.created_at)
            ).label("avg_duration_seconds")
        ).where(
            and_(
                Mission.user_id == user_id,
                Mission.status == "completed"
            )
        )
        
        duration_result = await session.execute(duration_query)
        avg_duration_seconds = duration_result.scalar()
        
        if avg_duration_seconds:
            # تحويل من ثواني إلى ساعات
            performance["average_mission_duration_hours"] = avg_duration_seconds / 3600
        else:
            performance["average_mission_duration_hours"] = 0.0
        
        # المهام في الأسبوع (Missions per Week)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_missions_query = select(func.count(Mission.id)).where(
            and_(
                Mission.user_id == user_id,
                Mission.created_at >= seven_days_ago
            )
        )
        
        recent_result = await session.execute(recent_missions_query)
        performance["missions_per_week"] = recent_result.scalar() or 0
        
        # درجة الإنتاجية (Productivity Score)
        productivity = min(completed * 10, 100)
        performance["productivity_score"] = productivity
        
        # درجة الجودة (Quality Score)
        quality = performance["success_rate"]
        performance["quality_score"] = min(quality, 100)
        
        logger.info(f"Retrieved performance metrics for user {user_id}")
        return performance
        
    except Exception as e:
        logger.error(f"Error getting performance for user {user_id}: {e}")
        return {}
