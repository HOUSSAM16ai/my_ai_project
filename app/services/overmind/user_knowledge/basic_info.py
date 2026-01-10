"""
إدارة المعلومات الأساسية للمستخدمين (User Basic Information Management).

يوفر الوصول إلى المعلومات الأساسية للمستخدمين من قاعدة البيانات.

المبادئ:
- Single Responsibility: فقط المعلومات الأساسية
- Error Handling: معالجة شاملة للأخطاء
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di import get_logger
from app.core.domain.models import User

logger = get_logger(__name__)


async def get_user_basic_info(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    الحصول على المعلومات الأساسية للمستخدم.

    Args:
        session: جلسة قاعدة البيانات
        user_id: معرّف المستخدم

    Returns:
        dict: المعلومات الأساسية

    يشمل:
        - id: المعرّف الفريد
        - name: الاسم الكامل
        - email: البريد الإلكتروني
        - role: الدور (admin, user, guest)
        - is_active: نشط أم لا
        - is_verified: موثق أم لا
        - created_at: تاريخ الإنشاء
        - updated_at: آخر تحديث
    """
    try:
        # الاستعلام عن المستخدم
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User {user_id} not found")
            return {}

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_active": user.is_active if hasattr(user, 'is_active') else True,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else False,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
            "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None,
        }

    except Exception as e:
        logger.error(f"Error getting basic info for user {user_id}: {e}")
        return {}


async def list_all_users(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    عرض قائمة جميع المستخدمين مع معلومات مختصرة.

    Args:
        session: جلسة قاعدة البيانات
        limit: عدد المستخدمين المطلوب
        offset: الإزاحة (للصفحات)

    Returns:
        list[dict]: قائمة المستخدمين
    """
    try:
        # الاستعلام عن المستخدمين
        query = select(User).limit(limit).offset(offset)
        result = await session.execute(query)
        users = result.scalars().all()

        users_list = []
        for user in users:
            users_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "is_active": user.is_active if hasattr(user, 'is_active') else True,
            })

        logger.info(f"Listed {len(users_list)} users")
        return users_list

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return []
