"""
خدمة المستخدمين - الطبقة الأساسية لإدارة هويات النظام.

المعمارية (Architecture):
تتبع هذه الخدمة نمط "حقن التبعيات الصارم" (Strict Dependency Injection).
لا تقوم الخدمة بإنشاء جلسات قاعدة البيانات بنفسها، بل تتوقع استلام "وحدة عمل" (Unit of Work)
جاهزة ممثلة في `AsyncSession`.

المسؤوليات (Responsibilities):
1. إدارة دورة حياة المستخدم (إنشاء، تعديل، قراءة).
2. ضمان وجود المستخدم المسؤول (Admin Assurance).
3. تطبيق قواعد العمل (Business Rules) مثل منع تكرار البريد الإلكتروني.

ملاحظة: الدوال المستقلة في نهاية الملف توفر واجهة استخدام مريحة (Facade) للسكربتات
وأدوات سطر الأوامر (CLI) التي تعمل خارج نطاق حاوية الخدمات.
"""
from __future__ import annotations

from typing import Any


import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings
from app.core.database import async_session_factory
from app.models import User

logger = logging.getLogger(__name__)

class UserService:
    """
    خدمة إدارة المستخدمين المركزية.

    مصممة للعمل داخل نطاق الطلب (Request Scope) مع جلسة قاعدة بيانات محقونة.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: AppSettings | None = None,
    ) -> None:
        """
        تهيئة خدمة المستخدمين.

        Args:
            session: جلسة قاعدة البيانات النشطة (مطلوبة إلزامياً).
            settings: إعدادات التطبيق. في حال عدم توفرها، يتم تحميل الإعدادات الافتراضية.
        """
        self.session = session
        self.settings = settings or get_settings()

    async def get_all_users(self) -> Sequence[User]:
        """
        استرجاع قائمة كافة المستخدمين في النظام.

        Returns:
            Sequence[User]: قائمة كائنات المستخدمين مرتبة حسب المعرف.
        """
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_new_user(
        self, full_name: str, email: str, password: str, is_admin: bool = False
    ) -> dict[str, Any]:
        """
        إنشاء مستخدم جديد في النظام.

        Args:
            full_name: الاسم الكامل.
            email: البريد الإلكتروني (يجب أن يكون فريداً).
            password: كلمة المرور (سيتم تشفيرها).
            is_admin: صلاحية المسؤول.

        Returns:
            dict[str, Any]: نتيجة العملية (status, message).
        """
        # تسوية البريد الإلكتروني (Normalization)
        email = email.lower().strip()

        # 🛡️ Guard Clause: التحقق من وجود البريد الإلكتروني مسبقاً
        stmt = select(User).filter_by(email=email)
        result = await self.session.execute(stmt)
        if result.scalar():
            logger.warning(f"محاولة إنشاء مستخدم ببريد مكرر: {email}")
            return {
                "status": "error",
                "message": f"User with email '{email}' already exists.",
            }

        try:
            new_user = User(full_name=full_name, email=email, is_admin=is_admin)
            new_user.set_password(password)
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)

            admin_status = " (Admin)" if is_admin else ""
            success_message = f"User '{full_name}' created with ID {new_user.id}{admin_status}."
            logger.info(success_message)

            return {"status": "success", "message": success_message}

        except Exception as operation_error:
            await self.session.rollback()
            logger.error(f"فشل في إنشاء المستخدم: {operation_error}", exc_info=True)
            return {"status": "error", "message": str(operation_error)}

    async def ensure_admin_user_exists(self) -> dict[str, Any]:
        """
        ضمان وجود مستخدم بصلاحيات مسؤول (Admin) وفقاً لمتغيرات البيئة.
        تستخدم هذه الوظيفة عادة عند بدء تشغيل النظام.

        Returns:
            dict[str, Any]: نتيجة العملية.
        """
        admin_email = self.settings.ADMIN_EMAIL
        admin_password = self.settings.ADMIN_PASSWORD
        admin_name = self.settings.ADMIN_NAME

        # 🛡️ Guard Clause: التحقق من توفر متغيرات البيئة اللازمة
        if not all([admin_email, admin_password, admin_name]):
            logger.error("متغيرات بيئة المسؤول غير مضبوطة.")
            return {"status": "error", "message": "Admin environment variables not set."}

        try:
            # التحقق من وجود المستخدم
            stmt = select(User).filter_by(email=admin_email)
            result = await self.session.execute(stmt)
            existing_user = result.scalar()

            if existing_user:
                if existing_user.is_admin:
                    return {
                        "status": "success",
                        "message": f"Admin user '{admin_email}' already configured.",
                    }

                # ترقية المستخدم الحالي إلى مسؤول
                existing_user.is_admin = True
                await self.session.commit()
                logger.info(f"تمت ترقية المستخدم '{admin_email}' إلى مسؤول.")
                return {
                    "status": "success",
                    "message": f"User '{admin_email}' promoted to admin.",
                }

            # إنشاء مسؤول جديد
            # ملاحظة: نستخدم self.create_new_user لضمان توحيد المنطق، لكن هنا نحتاج التعامل المباشر
            # لتجنب تعقيد التداخل، ولأننا تحققنا بالفعل من عدم الوجود.
            new_admin = User(full_name=admin_name, email=admin_email, is_admin=True)
            new_admin.set_password(admin_password) # type: ignore
            self.session.add(new_admin)
            await self.session.commit()

            logger.info(f"تم إنشاء حساب المسؤول '{admin_email}'.")
            return {
                "status": "success",
                "message": f"Admin user '{admin_email}' created.",
            }

        except Exception as operation_error:
            await self.session.rollback()
            logger.error(
                f"خطأ أثناء التأكد من وجود المسؤول: {operation_error}", exc_info=True
            )
            return {"status": "error", "message": str(operation_error)}

# =============================================================================
# واجهات الاستخدام المستقلة (Standalone Facades)
# =============================================================================

async def get_all_users_async() -> list[User]:
    """
    واجهة غير متزامنة لاسترجاع كافة المستخدمين (للاستخدام في CLI/Scripts).
    تقوم بإنشاء جلسة قاعدة بيانات مؤقتة لهذه العملية فقط.
    """
    async with async_session_factory() as session:
        service = UserService(session)
        users = await service.get_all_users()
        return list(users)

async def create_new_user_async(
    full_name: str, email: str, password: str, is_admin: bool = False
) -> dict[str, Any]:
    """
    واجهة غير متزامنة لإنشاء مستخدم جديد (للاستخدام في CLI/Scripts).
    تقوم بإنشاء جلسة قاعدة بيانات مؤقتة لهذه العملية فقط.
    """
    async with async_session_factory() as session:
        service = UserService(session)
        return await service.create_new_user(full_name, email, password, is_admin)
