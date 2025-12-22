"""
نواة الواقع الإدراكي (Cognitive Reality Kernel).

هذه الوحدة تمثل نقطة الدخول المركزية لتطبيق FastAPI، مصممة وفقاً لأعلى معايير هندسة البرمجيات
(CS50 2025 Standards). توفر هذه النواة البنية التحتية اللازمة لربط كافة مكونات النظام ببعضها البعض.

المسؤوليات الأساسية:
1. بناء التطبيق (Application Factory Pattern).
2. إدارة التبعيات وحقن الإعدادات (Dependency Injection).
3. تكوين البرمجيات الوسيطة (Middleware Configuration).
4. استراتيجية توجيه المسارات (Routing Strategy).
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# استيراد الموجهات بشكل صريح لضمان الفشل السريع (Fail-Fast)
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

    تمثل هذه الفئة القلب النابض للنظام، حيث تقوم بتجميع كافة الأجزاء المتناثرة
    لخلق واقع برمجي متماسك وآمن.

    المبادئ التصميمية (Design Principles):
    - الصرامة في الأنواع (Strict Typing): استخدام أحدث ميزات Python 3.12+.
    - الوضوح (Explicitness): لا سحر خفي، كل شيء معرف بوضوح.
    - التوثيق الشامل (Comprehensive Documentation): شرح "لماذا" وليس فقط "كيف".

    Attributes:
        settings (AppSettings): إعدادات النظام التي تم التحقق منها بدقة.
        app (FastAPI): كائن التطبيق الرئيسي الجاهز للعمل.
    """

    def __init__(self, settings: AppSettings) -> None:
        """
        تهيئة نواة الواقع وبناء التكوين الأساسي.

        Args:
            settings: كائن الإعدادات الموثوق (AppSettings). لا نقبل القواميس العشوائية هنا
                      لضمان سلامة النوع (Type Safety) منذ اللحظة الأولى.
        """
        self.settings: Final[AppSettings] = settings

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

        يستخدم نمط `lifespan` لإدارة الموارد، وهو البديل الحديث والآمن لـ `on_event`.

        Returns:
            FastAPI: الكائن الأساسي للتطبيق قبل ربط المسارات.
        """

        @asynccontextmanager
        async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
            """
            مدير دورة الحياة (Lifespan Manager).
            ينظم عمليات بدء التشغيل والإيقاف بشكل متزامن وآمن.
            """
            # === [STARTUP] مرحلة الإطلاق ===
            logger.info("🚀 CogniForge System Initializing... (بدء تشغيل النظام)")

            # التحقق من قاعدة البيانات (يتم تخطيه في الاختبارات لتسريع التنفيذ)
            if self.settings.ENVIRONMENT != "testing":
                try:
                    # التحقق الصارم من مخطط قاعدة البيانات
                    await validate_schema_on_startup()
                    logger.info("✅ Database Schema Validated (تم التحقق من مخطط قاعدة البيانات)")
                except Exception as e:
                    # نسجل التحذير ولكن لا نوقف النظام للسماح بالتشغيل الجزئي في حالات الطوارئ القصوى
                    logger.warning(f"⚠️ Schema validation warning: {e}")

            logger.info("✅ System Ready (النظام جاهز)")

            yield  # نقطة تشغيل التطبيق (Serving Requests)

            # === [SHUTDOWN] مرحلة الإغلاق ===
            logger.info("👋 CogniForge System Shutting Down... (إيقاف النظام)")

        # تحديد بيئة التطوير لتفعيل الوثائق التفاعلية
        is_dev: bool = self.settings.ENVIRONMENT == "development"

        # تهيئة FastAPI مع البيانات الوصفية الكاملة
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

        الترتيب هنا مهم جداً لمعالجة الطلبات بشكل صحيح.

        Args:
            app: تطبيق FastAPI المراد حمايته وتحسينه.
        """
        # 1. المضيف الموثوق (Trusted Host): خط الدفاع الأول ضد هجمات Host Header Injection
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.settings.ALLOWED_HOSTS
        )

        # 2. مشاركة المصادر عبر المنشأ (CORS): ضبط سياسات الوصول من المتصفح
        self._configure_cors(app)

        # 3. ترويسات الأمان (Security Headers): إضافة طبقة حماية إضافية (HSTS, X-Frame-Options, etc.)
        app.add_middleware(SecurityHeadersMiddleware)

        # 4. تحديد المعدل (Rate Limiting): حماية النظام من الاستخدام المفرط (DDOS Protection)
        # يتم تعطيله في بيئة الاختبار لتجنب الإيجابيات الكاذبة أثناء الاختبارات المكثفة
        if self.settings.ENVIRONMENT != "testing":
            app.add_middleware(RateLimitMiddleware)

        # 5. تنظيف الترويسات (Clean Headers): إزالة الترويسات التي قد تعيق تقنيات مثل SSE
        app.add_middleware(RemoveBlockingHeadersMiddleware)

        # 6. ضغط البيانات (GZip Compression): تحسين الأداء عبر ضغط الردود النصية الكبيرة
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _configure_cors(self, app: FastAPI) -> None:
        """
        إعداد سياسات CORS (Cross-Origin Resource Sharing) بدقة.

        يتم التعامل مع CORS بحذر شديد لأنه ثغرة أمنية شائعة إذا تم تكوينه بشكل خاطئ.

        Args:
            app: التطبيق المراد تكوينه.
        """
        allow_origins: list[str] = self.settings.BACKEND_CORS_ORIGINS

        # استخدام منطق ذكي لتحديد الأصول المسموحة في حالة عدم التحديد الصريح
        if not allow_origins:
            if self.settings.ENVIRONMENT == "development":
                allow_origins = ["*"]  # سماح كامل في بيئة التطوير للتسهيل
            else:
                frontend_url = self.settings.FRONTEND_URL
                allow_origins = [frontend_url] if frontend_url else []

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            # نسمح بجميع الطرق القياسية
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            # نسمح بالترويسات الضرورية للمصادقة والأمان
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-CSRF-Token",
            ],
            # نكشف ترويسات معينة قد يحتاجها العميل
            expose_headers=["Content-Length", "Content-Range"],
        )

    def _weave_routes(self) -> None:
        """
        ربط الموجهات (Routers) بالتطبيق المركزي.

        يتم الربط بشكل صريح (Explicit) لضمان وضوح تدفق البيانات.
        كل مجموعة من المسارات لها بادئة (Prefix) خاصة بها لسهولة التمييز.
        """
        logger.info("Reality Kernel: Weaving explicit routes... (جاري ربط المسارات)")

        # 1. مسارات النظام (System Routes): الصحة، المعلومات
        # التوافر العالي (High Availability) يعتمد على هذه المسارات
        self.app.include_router(system.router)

        # 2. مسارات الإدارة (Admin Routes): لوحة التحكم والعمليات الإدارية الحساسة
        self.app.include_router(admin.router)

        # 3. مسارات الأمان (Security Routes): بوابة الدخول والمصادقة
        self.app.include_router(security.router, prefix="/api/security")

        # 4. شبكة البيانات (Data Mesh): العمليات المتقدمة والتحليلات
        self.app.include_router(data_mesh.router, prefix="/api/v1/data-mesh")

        # 5. قابلية المراقبة (Observability): عيون النظام (Metrics & Tracing)
        self.app.include_router(observability.router, prefix="/api/observability")

        # 6. العمليات الأساسية (General CRUD): الواجهة البرمجية العامة للموارد
        self.app.include_router(crud.router, prefix="/api/v1")
