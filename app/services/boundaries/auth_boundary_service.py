"""
خدمة حدود المصادقة (Auth Boundary Service).

تمثل هذه الخدمة الواجهة الموحدة (Facade) لعمليات المصادقة، حيث تقوم بتنسيق منطق الأعمال
بين طبقة العرض (Router) وطبقة البيانات (Persistence).

المعايير المطبقة (Standards Applied):
- CS50 2025: توثيق عربي احترافي، صرامة في الأنواع.
- SOLID: فصل المسؤوليات (Separation of Concerns).
- Security First: تكامل مع درع الدفاع الزمني (Chrono-Kinetic Defense Shield).
"""

from __future__ import annotations

import datetime
import logging

import jwt
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.security.chrono_shield import chrono_shield
from app.services.rbac import RBACService, STANDARD_ROLE
from app.services.security.auth_persistence import AuthPersistence

logger = logging.getLogger(__name__)

__all__ = ["AuthBoundaryService"]

class AuthBoundaryService:
    """
    خدمة حدود المصادقة (Auth Boundary Service).

    المسؤوليات:
    - تنسيق عمليات تسجيل الدخول والتسجيل.
    - إدارة الرموز المميزة (JWT Management).
    - حماية النظام باستخدام درع كرونو (Chrono Shield Integration).
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        تهيئة خدمة المصادقة.

        Args:
            db (AsyncSession): جلسة قاعدة البيانات غير المتزامنة.
        """
        self.db = db
        self.persistence = AuthPersistence(db)
        self.settings = get_settings()

    async def register_user(
        self, full_name: str, email: str, password: str
    ) -> dict[str, object]:
        """
        تسجيل مستخدم جديد في النظام.

        الخطوات:
        1. التحقق من عدم وجود البريد الإلكتروني مسبقاً.
        2. إنشاء المستخدم عبر طبقة البيانات.
        3. إرجاع استجابة نجاح مهيئة.

        Args:
            full_name (str): الاسم الكامل.
            email (str): البريد الإلكتروني.
            password (str): كلمة المرور (سيتم تجزئتها).

        Returns:
            dict[str, object]: تفاصيل العملية والمستخدم المسجل.

        Raises:
            HTTPException: في حال وجود البريد الإلكتروني مسبقاً (400).
        """
        # التحقق من وجود المستخدم
        if await self.persistence.user_exists(email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # إنشاء مستخدم جديد (الافتراضي: ليس مسؤولاً)
        new_user = await self.persistence.create_user(
            full_name=full_name,
            email=email,
            password=password,
            is_admin=False,
        )
        rbac_service = RBACService(self.db)
        await rbac_service.ensure_seed()
        await rbac_service.assign_role(new_user, STANDARD_ROLE)

        return {
            "status": "success",
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "is_admin": new_user.is_admin,
            },
        }

    async def authenticate_user(
        self, email: str, password: str, request: Request
    ) -> dict[str, object]:
        """
        المصادقة على المستخدم وإصدار رمز الدخول (JWT).

        هذه العملية محمية بواسطة درع الدفاع الزمني (Chrono-Kinetic Shield) لمنع هجمات التخمين.

        Args:
            email (str): البريد الإلكتروني.
            password (str): كلمة المرور.
            request (Request): كائن الطلب الحالي (لأغراض التتبع الأمني).

        Returns:
            dict[str, object]: رمز الدخول (Access Token) وتفاصيل المستخدم.

        Raises:
            HTTPException: عند فشل المصادقة (401).
        """
        # 0. تفعيل درع الدفاع الزمني (فحص السماحية)
        await chrono_shield.check_allowance(request, email)

        # 1. جلب بيانات المستخدم
        user = await self.persistence.get_user_by_email(email)

        # 2. التحقق من كلمة المرور (مع الحماية من هجمات التوقيت)
        is_valid = False
        if user:
            try:
                is_valid = user.verify_password(password)
            except Exception as e:
                logger.error(f"Password verification error for user {user.id}: {e}")
                is_valid = False
        else:
            # التحقق الشبحي: استهلاك موارد المعالج لإخفاء حقيقة عدم وجود المستخدم
            chrono_shield.phantom_verify(password)
            is_valid = False

        if not is_valid:
            # تسجيل الأثر الحركي للفشل (Kinetic Impact)
            chrono_shield.record_failure(request, email)
            logger.warning(f"Failed login attempt for {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # نجاح: إعادة تعيين مستوى التهديد لهذا الهدف
        chrono_shield.reset_target(email)

        # 3. توليد رمز JWT
        role = "admin" if user.is_admin else "user"
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": role,
            "is_admin": user.is_admin,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24),
        }

        token = jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

        landing_path = "/admin" if user.is_admin else "/app/chat"
        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "is_admin": user.is_admin,
            },
            "status": "success",
            "landing_path": landing_path,
        }

    async def get_current_user(self, token: str) -> dict[str, object]:
        """
        جلب بيانات المستخدم الحالي من رمز JWT.

        Args:
            token (str): رمز JWT الخام.

        Returns:
            dict[str, object]: تفاصيل المستخدم.

        Raises:
            HTTPException: إذا كان الرمز غير صالح أو المستخدم غير موجود.
        """
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        except jwt.PyJWTError as e:
            logger.warning(f"Token decoding failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token") from e

        user = await self.persistence.get_user_by_id(int(user_id))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "is_admin": user.is_admin,
        }

    @staticmethod
    def extract_token_from_request(request: Request) -> str:
        """
        استخراج رمز JWT من ترويسة التفويض (Authorization Header).

        Args:
            request (Request): طلب HTTP الوارد.

        Returns:
            str: الرمز المستخرج.

        Raises:
            HTTPException: إذا كانت الترويسة مفقودة أو التنسيق غير صحيح.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Invalid Authorization header format"
            )
        return parts[1]
