"""
Kernel

هذا الملف جزء من مشروع CogniForge.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import Routers explicitly
# Routers - استيراد المسارات المتاحة فقط
try:
    from app.api.routers import system
except ImportError:
    system = None

try:
    from app.api.routers import admin
except ImportError:
    admin = None

try:
    from app.api.routers import security
except ImportError:
    security = None

try:
    from app.api.routers import data_mesh
except ImportError:
    data_mesh = None

try:
    from app.api.routers import observability
except ImportError:
    observability = None

try:
    from app.api.routers import crud
except ImportError:
    crud = None

from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


class RealityKernel:
    """
    نواة الواقع الإدراكي - الإصدار الرابع (Cognitive Reality Weaver V4).

    النسخة المبسطة (Simplified Version):
    تم إزالة الطبقات السحرية (Magic Layers) مثل التحميل الديناميكي للمخططات (Dynamic Blueprints).
    الآن، كل شيء واضح وصريح (Explicit is better than implicit).

    المسؤوليات الرئيسية (الدور):
    1. **مصنع التطبيق (Application Factory)**: هو الذي يقوم بإنشاء "القلب" النابض للنظام (تطبيق FastAPI).
    2. **قائد الأوركسترا (Middleware Orchestration)**: يرتب الطبقات الأمنية والتحسينات (Middleware) لضمان حماية النظام وسرعته.
    3. **إدارة دورة الحياة (Lifespan Management)**: يتحكم في لحظة تشغيل النظام (الولادة) ولحظة إيقافه بسلام (الوفاة).
    4. **حائك المسارات (Route Weaver)**: يربط المسارات (Routers) بشكل مباشر.
    """

    def __init__(self, settings: dict[str, Any]):
        """
        تهيئة نواة الواقع (The Constructor).
        """
        self.settings = settings
        self.app: FastAPI = self._create_pristine_app()
        self._weave_routes()

    def get_app(self) -> FastAPI:
        """يعيد تطبيق FastAPI الجاهز والمنسوج بالكامل (The Fully Woven App)."""
        return self.app

    def _create_pristine_app(self) -> FastAPI:
        """
        ينشئ النسخة الأساسية من تطبيق FastAPI مع كل الإعدادات والطبقات اللازمة.
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """مدير دورة الحياة - ما يحدث عند التشغيل وعند الإغلاق."""
            async for _ in self._handle_lifespan_events():
                yield

        # تهيئة FastAPI (تجهيز الإطار العام)
        app = FastAPI(
            title=self.settings.get("PROJECT_NAME", "CogniForge"),
            version="v4.1-simplified",
            docs_url=(
                "/docs" if self.settings.get("ENVIRONMENT") == "development" else None
            ),
            redoc_url=(
                "/redoc" if self.settings.get("ENVIRONMENT") == "development" else None
            ),
            lifespan=lifespan,
        )

        self._configure_middleware(app)
        add_error_handlers(app)

        return app

    async def _handle_lifespan_events(self):
        """ينفذ المهام الضرورية عند بدء التشغيل وعند الإيقاف."""
        # === لحظة التشغيل (STARTUP) ===
        logger.info("🚀 CogniForge starting up... (النظام يبدأ العمل)")

        # التحقق من صحة هيكل قاعدة البيانات (يتم تخطيه في الاختبارات للسرعة)
        if self.settings.get("ENVIRONMENT") != "testing":
            try:
                # استيراد الوظيفة هنا لتجنب المشاكل الدائرية (Circular Imports)
                from app.core.database import validate_schema_on_startup

                await validate_schema_on_startup()
            except Exception as e:
                logger.warning(f"⚠️ Schema validation skipped or failed: {e}")

        logger.info(
            "✅ CogniForge ready to serve requests (النظام جاهز لاستقبال الطلبات)"
        )

        yield  # النظام يعمل الآن هنا

        # === لحظة الإيقاف (SHUTDOWN) ===
        logger.info("👋 CogniForge shutting down... (جاري إيقاف النظام)")

    def _configure_middleware(self, app: FastAPI):
        """تجهيز طبقات الحماية والتحسين (Middleware Stack)."""

        # 1. المضيف الموثوق (Trusted Host): لمنع الهجمات من نطاقات غير معروفة.
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=self.settings.get("ALLOWED_HOSTS", [])
        )

        # 2. مشاركة المصادر (CORS): للسماح للمتصفح بالاتصال من نطاقات محددة.
        self._configure_cors(app)

        # 3. ترويسات الأمان (Security Headers): إضافة دروع إضافية لردود الخادم.
        app.add_middleware(SecurityHeadersMiddleware)

        # 4. تحديد معدل الطلبات (Rate Limiting): لمنع الإغراق (DDOS) - معطل أثناء الاختبار.
        if self.settings.get("ENVIRONMENT") != "testing":
            app.add_middleware(RateLimitMiddleware)

        # 5. تنظيف الترويسات (Remove Blocking Headers): لضمان التوافق مع بيئات التطوير.
        app.add_middleware(RemoveBlockingHeadersMiddleware)

        # 6. ضغط البيانات (GZip): لتقليل حجم البيانات المرسلة وتسريع النظام.
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _configure_cors(self, app: FastAPI):
        """إعدادات CORS بناءً على البيئة (تطوير أو إنتاج)."""
        raw_origins = self.settings.get("BACKEND_CORS_ORIGINS", [])
        allow_origins = raw_origins if isinstance(raw_origins, list) else []

        # إذا لم يتم تحديد مصادر، نستخدم القيم الافتراضية الذكية
        if not allow_origins:
            if self.settings.get("ENVIRONMENT") == "development":
                allow_origins = ["*"]  # السماح للكل في التطوير
            else:
                allow_origins = [self.settings.get("FRONTEND_URL")]

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

    def _weave_routes(self):
        """
        ربط المسارات (Routers) بالتطبيق
        
        يربط فقط المسارات المتاحة لتجنب الأخطاء
        """
        logger.info("Reality Kernel: Weaving explicit routes.")

        # ربط المسارات المتاحة فقط
        if system:
            self.app.include_router(system.router)
            logger.info("✅ System routes connected")

        # Admin Routes
        if admin:
            self.app.include_router(admin.router)

        # Security Routes (prefixed with /api/security usually, checking original blueprint)
        if security:
            self.app.include_router(security.router, prefix="/api/security")

        # Data Mesh
        if data_mesh:
            self.app.include_router(data_mesh.router, prefix="/data-mesh")

        # Observability
        if observability:
            self.app.include_router(observability.router, prefix="/observability")

        # CRUD / API v1
        if crud:
            self.app.include_router(crud.router, prefix="/api/v1")
