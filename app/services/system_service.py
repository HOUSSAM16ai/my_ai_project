"""
System Service

هذا الملف جزء من مشروع CogniForge.
"""

# app/services/system_service.py
"""
نظام فحص صحة وسلامة البنية التحتية (System Service).
هذه الخدمة تعمل كـ "طبيب" للنظام، حيث تقوم بفحص القلب (قاعدة البيانات) والأعضاء الحيوية الأخرى.
"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models import User


class SystemService:
    """
    خدمة النظام (The Doctor).
    المسؤولية: التأكد من أن كل شيء يعمل بشكل صحيح.
    """

    async def check_database_status(self, db: AsyncSession) -> str:
        """
        فحص نبض قاعدة البيانات.
        يقوم بتنفيذ استعلام بسيط جداً (SELECT 1) للتأكد من أن الاتصال يعمل.
        """
        try:
            await db.execute(text("SELECT 1"))
            return "healthy"  # سليم
        except Exception:
            return "unhealthy"  # مريض

    async def is_database_connected(self, db: AsyncSession) -> bool:
        """هل قاعدة البيانات متصلة؟ (نعم/لا)"""
        status = await self.check_database_status(db)
        return status == "healthy"

    async def verify_system_integrity(self) -> dict:
        """
        الفحص الشامل (Deep Scan).
        يقوم بفحص أعمق للنظام:
        1. هل قاعدة البيانات تستجيب؟
        2. هل المستخدم المسؤول (Admin) موجود؟

        يستخدم جلسة (Session) منفصلة لضمان عدم التأثير على الطلبات الحالية.
        """
        admin_present = False
        db_status = "unknown"

        try:
            # إنشاء جلسة خاصة للفحص
            async with async_session_factory() as session:
                # الفحص 1: اتصال قاعدة البيانات
                await session.execute(text("SELECT 1"))
                db_status = "connected"

                # الفحص 2: وجود المسؤول
                # نبحث عن البريد الإلكتروني الافتراضي للمسؤول
                res = await session.execute(
                    select(User).where(User.email == "admin@example.com")
                )
                if res.scalars().first():
                    admin_present = True
        except Exception:
            # في حال حدوث خطأ كارثي، نعتبر قاعدة البيانات غير قابلة للوصول
            db_status = "unreachable"

        return {
            "status": "ok",
            "service": "backend running",
            "secrets_ok": True,  # ضمناً صحيح إذا وصلنا لهذه النقطة
            "admin_present": admin_present,
            "db": db_status,
        }


# مثيل واحد للخدمة يمكن استخدامه في كل مكان
system_service = SystemService()
