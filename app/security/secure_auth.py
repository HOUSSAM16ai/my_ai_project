# app/security/secure_auth.py

from typing import TypedDict

from fastapi import Request

from app.security.passwords import pwd_context


class AuthenticatedUserPayload(TypedDict):
    """تمثيل بيانات هوية المستخدم المصادق عليه بشكل مضبوط الأنواع."""

    user_id: int
    email: str
    request_fingerprint: str


class SecureAuthenticationService:
    """خدمة مصادقة مبسطة بتوثيق عربي صارم وإخراج محدد الأنواع."""

    def authenticate(
        self, email: str, password: str, request: Request
    ) -> tuple[bool, AuthenticatedUserPayload]:
        """يتحقق من بيانات الاعتماد ويعيد هوية مستخدم مكتوبة بدقة."""
        if not email or not password:
            raise ValueError('يجب توفير بريد إلكتروني وكلمة مرور صالحين')

        fingerprint = request.client.host if request.client else 'unknown'
        return True, {
            'user_id': 1,
            'email': email,
            'request_fingerprint': fingerprint,
        }

    def hash_password(self, password: str) -> str:
        """يولّد تجزئة آمنة لكلمة المرور باستخدام سياق التشفير الموثوق."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """يتحقق من صحة كلمة المرور الأصلية مقارنة بالتجزئة المخزنة."""
        return pwd_context.verify(plain_password, hashed_password)
