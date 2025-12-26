"""
نقطة الدخول الرئيسية لتطبيق CogniForge (Main Entry Point).

يتعامل مع تهيئة التطبيق، نسج البرمجيات الوسيطة، وخدمة الملفات الثابتة.

المبادئ (Principles):
- Harvard CS50 2025: توثيق عربي احترافي، وضوح الكود
- Berkeley SICP: Application Factory Pattern (دالة مصنع للتطبيق)
- SOLID: Single Responsibility (كل دالة لها مسؤولية واحدة)

البنية (Architecture):
    1. تحميل الإعدادات من .env
    2. إنشاء Kernel (النواة المركزية)
    3. نسج Middleware Stack
    4. ربط Routers
    5. إعداد Static Files
    6. تفعيل Health Monitoring
"""
import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.di import get_settings
from app.core.static_handler import setup_static_files
from app.kernel import RealityKernel
from app.services.system.system_service import system_service

# Load .env file before anything else
load_dotenv()

logger = logging.getLogger(__name__)

# --- Kernel Singleton ---
# This ensures the kernel is created only once.
_kernel_instance = None


def get_kernel():
    """
    الحصول على مثيل النواة (Kernel Singleton).
    
    يضمن إنشاء النواة مرة واحدة فقط (Singleton Pattern) للحفاظ على الحالة
    وتجنب إعادة التهيئة المكلفة.
    
    Returns:
        RealityKernel: مثيل النواة المركزية
    """
    global _kernel_instance
    if _kernel_instance is None:
        # تمرير كائن الإعدادات الكامل للحفاظ على أمان الأنواع
        settings = get_settings()
        # Refactoring: Using keyword arguments for Static Connascence
        _kernel_instance = RealityKernel(settings=settings)
    return _kernel_instance


async def _health_check():
    """
    فحص صحة النظام (Health Check).
    
    يفوض العملية إلى SystemService للتحقق من سلامة النظام بالكامل.
    
    Returns:
        تقرير حالة النظام
    """
    return await system_service.verify_system_integrity()


def _setup_monitoring(app: FastAPI):
    """
    إعداد نقاط نهاية المراقبة (Monitoring Endpoints).
    
    يضيف endpoint للفحص الصحي للنظام.
    
    Args:
        app: تطبيق FastAPI
    """
    app.add_api_route("/health", _health_check, methods=["GET"])


def create_app(static_dir: str | None = None) -> FastAPI:
    """
    دالة مصنع التطبيق (Application Factory) - الانفجار الكبير للتطبيق.

    هذه الدالة مسؤولة عن تهيئة دورة حياة التطبيق بالكامل:
    1. إنشاء مثيل النواة (Reality Kernel) - المحرك المركزي
    2. نسج البرمجيات الوسيطة (Security, CORS, Logging, etc.)
    3. ربط الموجهات ونقاط نهاية API
    4. إعداد خدمة الملفات الثابتة للواجهة الأمامية
    5. تفعيل مراقبة صحة النظام

    Args:
        static_dir: مسار اختياري لمجلد الملفات الثابتة (مفيد للاختبارات)

    Returns:
        FastAPI: مثيل تطبيق FastAPI مُهيأ بالكامل وجاهز لخدمة الطلبات
        
    المبدأ (Principle):
        Factory Pattern من SICP - إنشاء كائنات معقدة بطريقة منظمة
    """
    kernel = get_kernel()
    app = kernel.get_app()
    app.kernel = kernel  # type: ignore

    _setup_monitoring(app)
    # تفويض إعداد الملفات الثابتة إلى المعالج الأساسي
    setup_static_files(app, static_dir)

    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

# log startup
if hasattr(app, "logger"):
    app.logger.info("Application initialized with unified kernel middleware stack.")

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
