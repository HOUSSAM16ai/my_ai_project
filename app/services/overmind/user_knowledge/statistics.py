"""
إدارة إحصائيات المستخدمين (User Statistics Management).

يوفر الإحصائيات والنشاطات للمستخدمين.

المبادئ:
- Single Responsibility: فقط الإحصائيات
- Performance: استعلامات محسّنة
"""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.core.domain.models import ChatMessage, Mission, Task

logger = get_logger(__name__)


async def get_user_statistics(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    الحصول على إحصائيات المستخدم.
    
    Args:
        session: جلسة قاعدة البيانات
        user_id: معرّف المستخدم
        
    Returns:
        dict: إحصائيات شاملة
        
    يشمل:
        - total_missions: إجمالي المهام
        - active_missions: المهام النشطة
        - completed_missions: المهام المكتملة
        - failed_missions: المهام الفاشلة
        - total_tasks: إجمالي المهام الفرعية
        - completed_tasks: المهام المكتملة
        - total_chat_messages: إجمالي الرسائل
        - last_activity: آخر نشاط
    """
    try:
        stats = {}
        
        # إحصائيات المهام (Missions)
        missions_query = select(
            func.count(Mission.id).label("total"),
            func.sum(func.cast(Mission.status == "completed", int)).label("completed"),
            func.sum(func.cast(Mission.status == "failed", int)).label("failed"),
            func.sum(func.cast(Mission.status == "in_progress", int)).label("active"),
        ).where(Mission.user_id == user_id)
        
        missions_result = await session.execute(missions_query)
        missions_row = missions_result.one_or_none()
        
        if missions_row:
            stats["total_missions"] = missions_row.total or 0
            stats["completed_missions"] = missions_row.completed or 0
            stats["failed_missions"] = missions_row.failed or 0
            stats["active_missions"] = missions_row.active or 0
        else:
            stats["total_missions"] = 0
            stats["completed_missions"] = 0
            stats["failed_missions"] = 0
            stats["active_missions"] = 0
        
        # إحصائيات المهام الفرعية (Tasks)
        tasks_query = select(
            func.count(Task.id).label("total"),
            func.sum(func.cast(Task.status == "completed", int)).label("completed"),
        ).join(Mission).where(Mission.user_id == user_id)
        
        tasks_result = await session.execute(tasks_query)
        tasks_row = tasks_result.one_or_none()
        
        if tasks_row:
            stats["total_tasks"] = tasks_row.total or 0
            stats["completed_tasks"] = tasks_row.completed or 0
        else:
            stats["total_tasks"] = 0
            stats["completed_tasks"] = 0
        
        # إحصائيات الرسائل (Chat Messages)
        messages_query = select(func.count(ChatMessage.id)).where(
            ChatMessage.user_id == user_id
        )
        messages_result = await session.execute(messages_query)
        stats["total_chat_messages"] = messages_result.scalar() or 0
        
        # آخر نشاط (Last Activity)
        last_message_query = select(ChatMessage.created_at).where(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at.desc()).limit(1)
        
        last_message_result = await session.execute(last_message_query)
        last_message = last_message_result.scalar_one_or_none()
        
        if last_message:
            stats["last_activity"] = last_message.isoformat()
        else:
            stats["last_activity"] = None
        
        logger.info(f"Retrieved statistics for user {user_id}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics for user {user_id}: {e}")
        return {}
