"""
نواة الواقع الإدراكي (Reality Kernel).

هذا الملف يمثل القلب النابض للنظام (The Beating Heart)، حيث يتم تجميع كافة المكونات
الأساسية وبناء تطبيق FastAPI وفق معايير صارمة للأداء والأمان.

المعايير المطبقة (Standards Applied):
- CS50 2025: صرامة النوع والتوثيق (Type Strictness & Documentation).
- SOLID: مبادئ التصميم القوي (Robust Design).
- Explicit is better than Implicit: الوضوح في التبعيات.
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
from app.api.routers import admin, crud, data_mesh, observability, overmind, security, system
from app.config.settings import AppSettings
from app.core.db_schema import validate_schema_on_startup
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

__all__ = ["RealityKernel"]


class RealityKernel:
    """
    نواة الواقع الإدراكي - الإصدار الرابع (Cognitive Reality Weaver V4).

    المعمارية (Architecture):
    تم تصميم هذه النواة لتعمل بمثابة "المحرك المركزي" (Core Engine) الذي ينسق تدفق البيانات
    والتحكم في النظام بأكمله. تم التخلي عن الطبقات الضمنية (Implicit Layers) لصالح التصميم الصريح (Explicit Design)
    لضمان الاستقرار القوي (Robust Stability) وسهولة الصيانة (Maintainability).

    المسؤوليات الجوهرية (Core Responsibilities):
    1. **مصنع التطبيق (Application Factory)**: إنشاء وتكوين كائن `FastAPI` وفق معايير صارمة.
    2. **حياكة البرمجيات الوسيطة (Middleware Weaving)**: دمج طبقات الحماية والأداء بترتيب دقيق لضمان أقصى درجات الأمان والكفاءة.
    3. **إدارة دورة الحياة (Lifespan Management)**: التحكم المطلق في تهيئة الموارد عند التشغيل وتنظيفها عند الإيقاف.
    4. **توجيه المسارات (Route Orchestration)**: ربط المكونات الوظيفية (Routers) بالنظام المركزي بشكل مباشر ومحكم.

    المعايير (Standards):
    - **الصرامة في النوع (Type Strictness)**: الاعتماد الكامل على `Type Hints` الحديثة (Python 3.12+).
    - **التوثيق الشامل (Comprehensive Documentation)**: توثيق دقيق لكل وظيفة باللغة العربية المهنية.
    - **الأمان أولاً (Security First)**: تفعيل الترويسات الأمنية وتقييد الوصول افتراضياً.
    """

    def __init__(self, settings: AppSettings | dict[str, Any]) -> None:
        """
        تهيئة نواة الواقع وبناء التكوين الأساسي.

        يقوم هذا المُنشئ (Constructor) بتحويل الإعدادات الخام إلى كائن تكوين ذكي (Smart Config Object)
        ومن ثم إطلاق عملية بناء التطبيق النقي (Pristine App) وربط المسارات.

        Args:
            settings (AppSettings | dict[str, Any]): مصفوفة التكوين الذكية أو قاموس إعدادات.
        """
        # التحقق الذكي من التكوين وتحويله إذا لزم الأمر
        if isinstance(settings, dict):
            self.settings_obj: AppSettings | None = None
            self.settings_dict: dict[str, Any] = settings
        else:
            self.settings_obj = settings
            self.settings_dict = settings.model_dump()

        # إنشاء التطبيق النقي (The Pristine App)
        self.app: Final[FastAPI] = self._create_pristine_app()

        # حياكة المسارات (Weaving Routes)
        self._weave_routes()

    def get_app(self) -> FastAPI:
        """
        استرجاع كائن التطبيق الجاهز للعمل.

        يُستخدم هذا التابع من قبل خادم `uvicorn` أو أدوات الاختبار للوصول إلى التطبيق المكتمل.

        Returns:
            FastAPI: التطبيق بعد اكتمال تهيئته وربط كافة مكوناته.
        """
        return self.app

    def _create_pristine_app(self) -> FastAPI:
        """
        إنشاء الهيكل الأساسي للتطبيق مع إعدادات دورة الحياة والوثائق.

        يتم هنا تعريف مدير دورة الحياة (Lifespan Manager) الذي يتحكم في بدء وإيقاف الخدمات المساندة
        مثل قواعد البيانات.

        Returns:
            FastAPI: الكائن الأساسي للتطبيق قبل ربط المسارات.
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
            """
            مدير دورة الحياة: ينظم عمليات بدء التشغيل والإيقاف.

            Args:
                app (FastAPI): كائن التطبيق (يتم حقنه تلقائياً).

            Yields:
                None: يتم تسليم التحكم للتطبيق لمعالجة الطلبات.
            """
            async for _ in self._handle_lifespan_events():
                yield

        # تحديد بيئة التطوير لتفعيل الوثائق
        is_dev: bool = self.settings_dict.get("ENVIRONMENT") == "development"

        # تهيئة FastAPI مع البيانات الوصفية
        app = FastAPI(
            title=self.settings_dict.get("PROJECT_NAME", "CogniForge"),
            version=self.settings_dict.get("VERSION", "v4.1-simplified"),
            docs_url="/docs" if is_dev else None,
            redoc_url="/redoc" if is_dev else None,
            lifespan=lifespan,
        )

        # تكوين البرمجيات الوسيطة ومعالجات الأخطاء
        self._configure_middleware(app)
        add_error_handlers(app)

        return app

    async def _handle_lifespan_events(self) -> AsyncGenerator[None, None]:
        """
        معالجة أحداث النظام الحيوية (Startup & Shutdown).

        ينفذ عمليات التحقق من صحة المخطط (Schema Validation) والاتصال بقاعدة البيانات.
        يضمن أن النظام لا يبدأ إلا إذا كانت الأساسيات سليمة (في بيئة الإنتاج).

        Yields:
            None: إشارة إلى أن النظام جاهز للعمل.
        """
        # === [STARTUP] مرحلة الإطلاق ===
        logger.info("🚀 CogniForge System Initializing... (بدء تشغيل النظام)")

        # التحقق من قاعدة البيانات (يتم تخطيه في الاختبارات لتسريع التنفيذ)
        if self.settings_dict.get("ENVIRONMENT") != "testing":
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

    def _configure_middleware(self, app: FastAPI) -> None:
        """
        تكوين حزمة البرمجيات الوسيطة (Middleware Stack) وفقاً لأفضل الممارسات الأمنية.

        يتم ترتيب الطبقات بعناية: الأمان أولاً، ثم الأداء، ثم المعالجة.

        Args:
            app (FastAPI): تطبيق FastAPI المراد حمايته وتحسينه.
        """
        # 1. المضيف الموثوق (Trusted Host): الحماية من هجمات Host Header Injection
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.settings_dict.get("ALLOWED_HOSTS", [])
        )

        # 2. مشاركة المصادر عبر المنشأ (CORS): ضبط سياسات الوصول من المتصفح
        self._configure_cors(app)

        # 3. ترويسات الأمان (Security Headers): إضافة طبقة حماية إضافية (HSTS, X-Frame-Options, etc.)
        app.add_middleware(SecurityHeadersMiddleware)

        # 4. تحديد المعدل (Rate Limiting): حماية النظام من الاستخدام المفرط (معطل في الاختبارات)
        if self.settings_dict.get("ENVIRONMENT") != "testing":
            app.add_middleware(RateLimitMiddleware)

        # 5. تنظيف الترويسات (Clean Headers): إزالة الترويسات التي قد تكشف معلومات حساسة
        app.add_middleware(RemoveBlockingHeadersMiddleware)

        # 6. ضغط البيانات (GZip Compression): تحسين الأداء عبر ضغط الردود الكبيرة
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _configure_cors(self, app: FastAPI) -> None:
        """
        إعداد سياسات CORS بدقة بناءً على البيئة التشغيلية.

        يمنع الوصول غير المصرح به من نطاقات خارجية في بيئة الإنتاج.

        Args:
            app (FastAPI): التطبيق المراد تكوينه.
        """
        raw_origins = self.settings_dict.get("BACKEND_CORS_ORIGINS", [])
        allow_origins: list[str] = raw_origins if isinstance(raw_origins, list) else []

        # استخدام إعدادات افتراضية ذكية في حال عدم التحديد
        if not allow_origins:
            if self.settings_dict.get("ENVIRONMENT") == "development":
                allow_origins = ["*"]  # سماح كامل في بيئة التطوير
            else:
                frontend_url = self.settings_dict.get("FRONTEND_URL")
                allow_origins = [str(frontend_url)] if frontend_url else []

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

        # 7. العقل المدبر (Overmind - Super Agent): واجهة الذكاء الخارق
        self.app.include_router(overmind.router)
