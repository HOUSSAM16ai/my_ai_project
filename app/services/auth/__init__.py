"""
واجهة خدمة المصادقة العامة.
"""
from app.services.auth.schema import TokenBundle
from app.services.auth.service import AuthService

__all__ = ["AuthService", "TokenBundle"]
