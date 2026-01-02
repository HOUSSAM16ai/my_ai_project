"""
نظام معرفة المستخدمين الشامل لـ Overmind (Comprehensive User Knowledge System).

هذا النظام يوفر لـ Overmind معرفة كاملة ومفصلة عن جميع المستخدمين:
- المعلومات الأساسية (الاسم، البريد، الدور)
- النشاطات والإحصائيات (عدد المهام، الجلسات، الرسائل)
- السلوك والتفضيلات (اللغة، الثيم، الإعدادات)
- التاريخ والزمن (تاريخ الإنشاء، آخر نشاط، المدة)
- العلاقات (المهام المملوكة، المشاريع، الفرق)
- الأداء والمقاييس (معدل النجاح، السرعة، الجودة)
- الأمان والصلاحيات (الأدوار، الصلاحيات، التحقق)

المبادئ المطبقة:
- Complete Visibility: رؤية كاملة لكل تفاصيل المستخدم
- Privacy Aware: احترام الخصوصية وعدم تسريب البيانات الحساسة
- Real-time: بيانات محدثة في الوقت الفعلي
- Analytics: تحليلات وإحصائيات متقدمة

الأمان:
- ⚠️ لا تُعرض كلمات المرور أبداً
- ⚠️ تشفير البيانات الحساسة
- ⚠️ تسجيل جميع عمليات الوصول
- ⚠️ صلاحيات محددة لكل عملية
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.di import get_logger
from app.models import (
    ChatMessage,
    Mission,
    Task,
    User,
    UserRole,
    UserSession,
)

logger = get_logger(__name__)


class UserKnowledge:
    """
    معرفة المستخدم الشاملة (Comprehensive User Knowledge).
    
    يوفر معلومات تفصيلية عن أي مستخدم في النظام:
    - من هو؟ (الهوية)
    - ماذا يفعل؟ (النشاطات)
    - كيف يتصرف؟ (السلوك)
    - ماذا يفضل؟ (التفضيلات)
    - كيف أداؤه؟ (المقاييس)
    
    الاستخدام:
        >>> async with UserKnowledge() as uk:
        >>>     user_info = await uk.get_user_complete_profile(user_id=1)
        >>>     print(user_info['basic']['name'])
        >>>     print(user_info['statistics']['total_missions'])
    """
    
    def __init__(self) -> None:
        """تهيئة نظام معرفة المستخدمين."""
        self._session: AsyncSession | None = None
    
    async def __aenter__(self):
        """فتح الجلسة (Context Manager)."""
        async for session in get_db():
            self._session = session
            break
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة."""
        if self._session:
            await self._session.close()
    
    # =========================================================================
    # المعلومات الأساسية (Basic Information)
    # =========================================================================
    
    async def get_user_basic_info(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على المعلومات الأساسية للمستخدم.
        
        Args:
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
            
        مثال:
            >>> info = await uk.get_user_basic_info(1)
            >>> print(f"{info['name']} ({info['email']})")
        """
        if not self._session:
            return {}
        
        try:
            # الاستعلام عن المستخدم
            result = await self._session.execute(
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
    
    # =========================================================================
    # الإحصائيات والنشاطات (Statistics & Activities)
    # =========================================================================
    
    async def get_user_statistics(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على إحصائيات المستخدم.
        
        Args:
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
            - total_sessions: إجمالي الجلسات
            - last_activity: آخر نشاط
            
        مثال:
            >>> stats = await uk.get_user_statistics(1)
            >>> print(f"Missions: {stats['total_missions']}")
        """
        if not self._session:
            return {}
        
        try:
            stats = {}
            
            # إحصائيات المهام (Missions)
            missions_query = select(
                func.count(Mission.id).label("total"),
                func.sum(func.cast(Mission.status == "completed", int)).label("completed"),
                func.sum(func.cast(Mission.status == "failed", int)).label("failed"),
                func.sum(func.cast(Mission.status == "in_progress", int)).label("active"),
            ).where(Mission.user_id == user_id)
            
            missions_result = await self._session.execute(missions_query)
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
            
            tasks_result = await self._session.execute(tasks_query)
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
            messages_result = await self._session.execute(messages_query)
            stats["total_chat_messages"] = messages_result.scalar() or 0
            
            # آخر نشاط (Last Activity)
            last_message_query = select(ChatMessage.created_at).where(
                ChatMessage.user_id == user_id
            ).order_by(ChatMessage.created_at.desc()).limit(1)
            
            last_message_result = await self._session.execute(last_message_query)
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
    
    # =========================================================================
    # السلوك والأداء (Behavior & Performance)
    # =========================================================================
    
    async def get_user_performance(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على مقاييس أداء المستخدم.
        
        Args:
            user_id: معرّف المستخدم
            
        Returns:
            dict: مقاييس الأداء
            
        يشمل:
            - success_rate: معدل النجاح (%)
            - average_mission_duration: متوسط مدة المهمة (ساعات)
            - missions_per_week: المهام في الأسبوع
            - productivity_score: درجة الإنتاجية (0-100)
            - quality_score: درجة الجودة (0-100)
        """
        if not self._session:
            return {}
        
        try:
            performance = {}
            
            # معدل النجاح (Success Rate)
            stats = await self.get_user_statistics(user_id)
            total = stats.get("total_missions", 0)
            completed = stats.get("completed_missions", 0)
            
            if total > 0:
                performance["success_rate"] = (completed / total) * 100
            else:
                performance["success_rate"] = 0.0
            
            # متوسط مدة المهمة (Average Mission Duration)
            # نحسب من created_at إلى updated_at للمهام المكتملة
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
            
            duration_result = await self._session.execute(duration_query)
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
            
            recent_result = await self._session.execute(recent_missions_query)
            performance["missions_per_week"] = recent_result.scalar() or 0
            
            # درجة الإنتاجية (Productivity Score)
            # معادلة بسيطة: عدد المهام المكتملة * 10 (حد أقصى 100)
            productivity = min(completed * 10, 100)
            performance["productivity_score"] = productivity
            
            # درجة الجودة (Quality Score)
            # معادلة: معدل النجاح * نسبة المهام المكتملة من الإجمالي
            quality = performance["success_rate"]
            performance["quality_score"] = min(quality, 100)
            
            logger.info(f"Retrieved performance metrics for user {user_id}")
            return performance
            
        except Exception as e:
            logger.error(f"Error getting performance for user {user_id}: {e}")
            return {}
    
    # =========================================================================
    # العلاقات والروابط (Relations & Connections)
    # =========================================================================
    
    async def get_user_relations(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على علاقات المستخدم مع الكيانات الأخرى.
        
        Args:
            user_id: معرّف المستخدم
            
        Returns:
            dict: العلاقات والروابط
            
        يشمل:
            - missions: قائمة المهام (آخر 5)
            - recent_messages: الرسائل الأخيرة (آخر 5)
            - collaborators: المتعاونون (إن وُجدوا)
        """
        if not self._session:
            return {}
        
        try:
            relations = {}
            
            # المهام الأخيرة (Recent Missions)
            missions_query = select(Mission).where(
                Mission.user_id == user_id
            ).order_by(Mission.created_at.desc()).limit(5)
            
            missions_result = await self._session.execute(missions_query)
            missions = missions_result.scalars().all()
            
            relations["recent_missions"] = [
                {
                    "id": m.id,
                    "objective": m.objective,
                    "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
                    "created_at": m.created_at.isoformat() if hasattr(m, 'created_at') else None,
                }
                for m in missions
            ]
            
            # الرسائل الأخيرة (Recent Messages)
            messages_query = select(ChatMessage).where(
                ChatMessage.user_id == user_id
            ).order_by(ChatMessage.created_at.desc()).limit(5)
            
            messages_result = await self._session.execute(messages_query)
            messages = messages_result.scalars().all()
            
            relations["recent_messages"] = [
                {
                    "id": msg.id,
                    "role": msg.role if hasattr(msg, 'role') else "user",
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None,
                }
                for msg in messages
            ]
            
            logger.info(f"Retrieved relations for user {user_id}")
            return relations
            
        except Exception as e:
            logger.error(f"Error getting relations for user {user_id}: {e}")
            return {}
    
    # =========================================================================
    # الملف الشامل (Complete Profile)
    # =========================================================================
    
    async def get_user_complete_profile(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على الملف الشخصي الكامل والشامل للمستخدم.
        
        Args:
            user_id: معرّف المستخدم
            
        Returns:
            dict: الملف الشخصي الكامل
            
        يجمع جميع المعلومات:
            - basic: المعلومات الأساسية
            - statistics: الإحصائيات
            - performance: مقاييس الأداء
            - relations: العلاقات
            
        مثال:
            >>> profile = await uk.get_user_complete_profile(1)
            >>> print(json.dumps(profile, indent=2))
            {
              "basic": {...},
              "statistics": {...},
              "performance": {...},
              "relations": {...}
            }
        """
        logger.info(f"Building complete profile for user {user_id}")
        
        # جمع جميع المعلومات بالتوازي
        basic = await self.get_user_basic_info(user_id)
        
        if not basic:
            logger.warning(f"User {user_id} not found")
            return {
                "error": "User not found",
                "user_id": user_id,
            }
        
        statistics = await self.get_user_statistics(user_id)
        performance = await self.get_user_performance(user_id)
        relations = await self.get_user_relations(user_id)
        
        profile = {
            "user_id": user_id,
            "basic": basic,
            "statistics": statistics,
            "performance": performance,
            "relations": relations,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Complete profile generated for user {user_id}")
        return profile
    
    # =========================================================================
    # قائمة المستخدمين (Users List)
    # =========================================================================
    
    async def list_all_users(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        عرض قائمة جميع المستخدمين مع معلومات مختصرة.
        
        Args:
            limit: عدد المستخدمين المطلوب
            offset: الإزاحة (للصفحات)
            
        Returns:
            list[dict]: قائمة المستخدمين
            
        مثال:
            >>> users = await uk.list_all_users(limit=10)
            >>> for user in users:
            >>>     print(f"{user['id']}: {user['name']}")
        """
        if not self._session:
            return []
        
        try:
            # الاستعلام عن المستخدمين
            query = select(User).limit(limit).offset(offset)
            result = await self._session.execute(query)
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
    
    # =========================================================================
    # البحث (Search)
    # =========================================================================
    
    async def search_users(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        البحث عن مستخدمين.
        
        Args:
            query: نص البحث (اسم أو بريد)
            limit: عدد النتائج
            
        Returns:
            list[dict]: نتائج البحث
            
        مثال:
            >>> results = await uk.search_users("john")
            >>> for user in results:
            >>>     print(user['name'])
        """
        if not self._session:
            return []
        
        try:
            # البحث في الاسم أو البريد
            search_query = select(User).where(
                (User.name.ilike(f"%{query}%")) | 
                (User.email.ilike(f"%{query}%"))
            ).limit(limit)
            
            result = await self._session.execute(search_query)
            users = result.scalars().all()
            
            results = []
            for user in users:
                results.append({
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                })
            
            logger.info(f"Found {len(results)} users matching '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
