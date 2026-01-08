"""
خدمة المصادقة المركزية (Deprecated).

تم نقل المنطق إلى `app.services.auth` للحصول على تصميم أكثر تفكيكًا وتنظيمًا.
يتم الاحتفاظ بهذا الملف للتوافق العكسي.
"""
from app.services.auth import AuthService, TokenBundle

__all__ = ["AuthService", "TokenBundle"]
