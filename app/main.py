"""
نقطة الدخول الرئيسية لتطبيق CogniForge (Main Entry Point).

تم التبسيط بشكل جذري لتكون نقطة انطلاق خالية من المنطق (Logic-Free Bootstrapper).
المسؤولية الكاملة للتكوين والتهيئة تقع الآن على عاتق `RealityKernel`.

المبادئ:
- Separation of Concerns: ملف main.py فقط للتشغيل.
- Singleton Pattern: يتم الحصول على النواة عبر الكائن النهائي.
"""

from app.core.config import AppSettings, get_settings
from app.kernel import RealityKernel
from app.middleware.static_files_middleware import StaticFilesConfig, setup_static_files_middleware
from fastapi import FastAPI

# 1. تهيئة الإعدادات
settings = get_settings()

# 2. بدء تشغيل النواة (Boot The Kernel)
_kernel = RealityKernel(settings=settings)

# 3. تصدير كائن التطبيق (ASGI Interface)
app = _kernel.get_app()


def create_app(
    *,
    settings_override: "AppSettings | None" = None,
    static_dir: str | None = None,
    enable_static_files: bool = True,
) -> FastAPI:
    """
    مصنع تطبيق مرن يسمح بالتهيئة حسب الحاجة دون تعديل الحالة العالمية.

    الأهداف:
    - دعم تمارين الاختبار التي تحتاج لمسارات ثابتة مخصصة.
    - احترام مبدأ التركيب الوظيفي عبر بناء النواة ثم إضافة واجهة الملفات الثابتة اختيارياً.
    """

    effective_settings = settings_override or get_settings()
    delegate_static = enable_static_files and static_dir is None
    kernel = RealityKernel(settings=effective_settings, enable_static_files=delegate_static)
    application = kernel.get_app()

    if enable_static_files and not delegate_static:
        static_config = StaticFilesConfig(static_dir=static_dir)
        setup_static_files_middleware(application, static_config)

    return application
