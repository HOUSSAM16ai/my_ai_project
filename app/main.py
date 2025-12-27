"""
نقطة الدخول الرئيسية لتطبيق CogniForge (Main Entry Point).

تم التبسيط بشكل جذري لتكون نقطة انطلاق خالية من المنطق (Logic-Free Bootstrapper).
المسؤولية الكاملة للتكوين والتهيئة تقع الآن على عاتق `RealityKernel`.

المبادئ:
- Separation of Concerns: ملف main.py فقط للتشغيل.
- Singleton Pattern: يتم الحصول على النواة عبر الكائن النهائي.
"""

from app.config.settings import get_settings
from app.kernel import RealityKernel

# 1. تهيئة الإعدادات
settings = get_settings()

# 2. بدء تشغيل النواة (Boot The Kernel)
_kernel = RealityKernel(settings=settings)

# 3. تصدير كائن التطبيق (ASGI Interface)
app = _kernel.get_app()
