"""
نواة الواقع الإدراكي (Cognitive Reality Kernel).

هذه الوحدة تمثل نقطة الدخول المركزية لتطبيق FastAPI.
تتبع معايير CS50 2025 في التصميم والتوثيق والنوعية.

المسؤوليات:
1. بناء التطبيق (Factory Pattern).
2. إدارة التبعيات (Dependency Injection via Settings).
3. تكوين البرمجيات الوسيطة (Middleware Configuration).
4. توجيه المسارات (Routing Strategy).
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# استيراد الموجهات بشكل صريح لضمان الفشل السريع عند فقدان أي تبعية
# Explicit Import of Routers to ensure Fast Failure if dependencies are missing
from app.api.routers import admin, crud, data_mesh, observability, security, system
from app.config.settings import AppSettings
from app.core.database import validate_schema_on_startup
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

__all__ = ["RealityKernel"]

logger = logging.getLogger(__name__)


class RealityKernel:
    """
    نواة الواقع الإدراكي - الإصدار الخامس (Cognitive Reality Weaver V5).

    تم تحديث المعمارية لتوافق مبادئ CS50 2025:
    - صرامة عالية في الأنواع (Strict Typing).
    - وضوح تام في المسؤوليات (Explicit Responsibilities).
    - توثيق عربي احترافي (Professional Arabic Documentation).

    Attributes:
        settings (AppSettings): إعدادات النظام التي تم التحقق منها.
        app (FastAPI): كائن التطبيق الرئيسي.
    """

    def __init__(self, settings: AppSettings | dict[str, Any]) -> None:
        """
        تهيئة نواة الواقع وبناء التكوين الأساسي.

        يقوم المُشيد (Constructor) بتحويل القاموس إلى كائن إعدادات صارم إذا لزم الأمر،
        ثم يبدأ عملية بناء التطبيق.

        Args:
            settings: إعدادات التطبيق. يفضل استخدام `AppSettings` مباشرة.
                      دعم `dict` موجود للتوافق مع الأنظمة القديمة ولكن سيتم إزالته مستقبلاً.
        """
        # التحقق الذكي من التكوين وتحويله إذا لزم الأمر
        if isinstance(settings, dict):
            # Legacy Support Warning could be added here
            self.settings: AppSettings = AppSettings(**settings)
        else:
            self.settings = settings

        # إنشاء التطبيق النقي (The Pristine App)
        self.app: Final[FastAPI] = self._create_pristine_app()

        # حياكة المسارات (Weaving Routes)
        self._weave_routes()

    def get_app(self) -> FastAPI:
        """
        استرجاع كائن التطبيق الجاهز للعمل.

        Returns:
            FastAPI: التطبيق بعد اكتمال تهيئته وربط كافة مكوناته.
        """
        return self.app

    def _create_pristine_app(self) -> FastAPI:
        """
        إنشاء الهيكل الأساسي للتطبيق مع إعدادات دورة الحياة والوثائق.

        يستخدم نمط `lifespan` لإدارة الموارد بدلاً من `on_event` القديمة.

        Returns:
            FastAPI: الكائن الأساسي للتطبيق قبل ربط المسارات.
        """

        @asynccontextmanager
        async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
            """مدير دورة الحياة: ينظم عمليات بدء التشغيل والإيقاف."""
            # === [STARTUP] مرحلة الإطلاق ===
            logger.info("🚀 CogniForge System Initializing... (بدء تشغيل النظام)")

            # التحقق من قاعدة البيانات (يتم تخطيه في الاختبارات لتسريع التنفيذ)
            if self.settings.ENVIRONMENT != "testing":
                try:
                    # التحقق الصارم من مخطط قاعدة البيانات
                    await validate_schema_on_startup()
                    logger.info("✅ Database Schema Validated (تم التحقق من مخطط قاعدة البيانات)")
                except Exception as e:
                    # نسجل التحذير ولكن لا نوقف النظام للسماح بالتشغيل الجزئي في حالات الطوارئ
                    logger.warning(f"⚠️ Schema validation warning: {e}")

            logger.info("✅ System Ready (النظام جاهز)")

            yield  # نقطة تشغيل التطبيق (Serving Requests)

            # === [SHUTDOWN] مرحلة الإغلاق ===
            logger.info("👋 CogniForge System Shutting Down... (إيقاف النظام)")

        # تحديد بيئة التطوير لتفعيل الوثائق
        is_dev: bool = self.settings.ENVIRONMENT == "development"

        # تهيئة FastAPI مع البيانات الوصفية
        app = FastAPI(
            title=self.settings.PROJECT_NAME,
            version=self.settings.VERSION,
            description=self.settings.DESCRIPTION,
            docs_url="/docs" if is_dev else None,
            redoc_url="/redoc" if is_dev else None,
            lifespan=lifespan,
        )

        # تكوين البرمجيات الوسيطة ومعالجات الأخطاء
        self._configure_middleware(app)
        add_error_handlers(app)

        return app

    def _configure_middleware(self, app: FastAPI) -> None:
        """
        تكوين حزمة البرمجيات الوسيطة (Middleware Stack) وفقاً لأفضل الممارسات الأمنية.

        Args:
            app: تطبيق FastAPI المراد حمايته وتحسينه.
        """
        # 1. المضيف الموثوق (Trusted Host): الحماية من هجمات Host Header Injection
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.settings.ALLOWED_HOSTS
        )

        # 2. مشاركة المصادر عبر المنشأ (CORS): ضبط سياسات الوصول من المتصفح
        self._configure_cors(app)

        # 3. ترويسات الأمان (Security Headers): إضافة طبقة حماية إضافية (HSTS, X-Frame-Options, etc.)
        app.add_middleware(SecurityHeadersMiddleware)

        # 4. تحديد المعدل (Rate Limiting): حماية النظام من الاستخدام المفرط (معطل في الاختبارات)
        if self.settings.ENVIRONMENT != "testing":
            app.add_middleware(RateLimitMiddleware)

        # 5. تنظيف الترويسات (Clean Headers): إزالة الترويسات التي قد تكشف معلومات حساسة أو تعيق الأداء
        app.add_middleware(RemoveBlockingHeadersMiddleware)

        # 6. ضغط البيانات (GZip Compression): تحسين الأداء عبر ضغط الردود الكبيرة
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _configure_cors(self, app: FastAPI) -> None:
        """
        إعداد سياسات CORS بدقة بناءً على البيئة التشغيلية.

        Args:
            app: التطبيق المراد تكوينه.
        """
        raw_origins = self.settings.BACKEND_CORS_ORIGINS
        # Pydantic already ensures this is a list[str], but extra safety fits the strictness theme
        allow_origins: list[str] = raw_origins

        # استخدام إعدادات افتراضية ذكية في حال عدم التحديد
        if not allow_origins:
            if self.settings.ENVIRONMENT == "development":
                allow_origins = ["*"]  # سماح كامل في بيئة التطوير
            else:
                frontend_url = self.settings.FRONTEND_URL
                allow_origins = [frontend_url] if frontend_url else []

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-CSRF-Token",
            ],
            expose_headers=["Content-Length", "Content-Range"],
        )

    def _weave_routes(self) -> None:
        """
        ربط الموجهات (Routers) بالتطبيق المركزي.

        يتم الربط بشكل صريح (Explicit) لضمان وضوح تدفق البيانات وسهولة التتبع.
        """
        logger.info("Reality Kernel: Weaving explicit routes... (جاري ربط المسارات)")

        # 1. مسارات النظام (System Routes): الصحة، المعلومات
        self.app.include_router(system.router)

        # 2. مسارات الإدارة (Admin Routes): لوحة التحكم والعمليات الإدارية
        self.app.include_router(admin.router)

        # 3. مسارات الأمان (Security Routes): المصادقة والتفويض
        self.app.include_router(security.router, prefix="/api/security")

        # 4. شبكة البيانات (Data Mesh): العمليات المتقدمة على البيانات
        self.app.include_router(data_mesh.router, prefix="/api/v1/data-mesh")

        # 5. قابلية المراقبة (Observability): التتبع والمقاييس
        self.app.include_router(observability.router, prefix="/api/observability")

        # 6. العمليات الأساسية (CRUD / API v1): الواجهة البرمجية العامة
        self.app.include_router(crud.router, prefix="/api/v1")
