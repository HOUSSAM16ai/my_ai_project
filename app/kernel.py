import importlib
import inspect
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.blueprints import Blueprint
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


class RealityKernel:
    """
    نواة الواقع الإدراكي - الإصدار الرابع (Cognitive Reality Weaver V4).

    تخيل أن هذا الكلاس (Class) هو "المدير العام" أو "العقل المدبر" للنظام بأكمله.
    هو المسؤول عن توصيل كل أجزاء النظام ببعضها البعض، تماماً مثل الجهاز العصبي في جسم الإنسان.

    المسؤوليات الرئيسية (الدور):
    1. **مصنع التطبيق (Application Factory)**: هو الذي يقوم بإنشاء "القلب" النابض للنظام (تطبيق FastAPI).
    2. **قائد الأوركسترا (Middleware Orchestration)**: يرتب الطبقات الأمنية والتحسينات (Middleware) لضمان حماية النظام وسرعته.
    3. **إدارة دورة الحياة (Lifespan Management)**: يتحكم في لحظة تشغيل النظام (الولادة) ولحظة إيقافه بسلام (الوفاة)، بما في ذلك الاتصال بقواعد البيانات.
    4. **حائك المسارات (Dynamic Routing)**: يكتشف "المخططات" (Blueprints) والمسارات تلقائياً ويربطها بالنظام بذكاء دون الحاجة لتعديل الكود الأساسي.

    لماذا هذا الكود موجود؟
    لفصل إعدادات التشغيل عن المنطق البرمجي، مما يجعل النظام قابلاً للاختبار، سهلاً في التعديل، ومنظماً بشكل خارق.
    """

    def __init__(self, settings: dict[str, Any]):
        """
        تهيئة نواة الواقع (The Constructor).

        هذه الدالة هي "نقطة البداية" للكلاس. تستقبل الإعدادات (Settings) كمدخلات.
        لماذا نمرر الإعدادات هنا؟ لكي نتمكن من تغييرها بسهولة (مثلاً، استخدام قاعدة بيانات تجريبية أثناء الاختبارات)
        بدلاً من الاعتماد على المتغيرات العامة التي يصعب تغييرها.

        المعاملات:
            settings (dict[str, Any]): قاموس يحتوي على أسرار وإعدادات التطبيق.
        """
        self.settings = settings
        self.app: FastAPI = self._create_pristine_app()
        self._discover_and_weave_blueprints()

    def get_app(self) -> FastAPI:
        """يعيد تطبيق FastAPI الجاهز والمنسوج بالكامل (The Fully Woven App)."""
        return self.app

    def _create_pristine_app(self) -> FastAPI:
        """
        ينشئ النسخة الأساسية من تطبيق FastAPI مع كل الإعدادات والطبقات اللازمة.
        هنا يتم تركيب "الدروع" (Middleware) وتجهيز "القلب".
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """مدير دورة الحياة - ما يحدث عند التشغيل وعند الإغلاق."""
            async for _ in self._handle_lifespan_events():
                yield

        # تهيئة FastAPI (تجهيز الإطار العام)
        app = FastAPI(
            title=self.settings.get("PROJECT_NAME", "CogniForge"),
            version="v4.0-woven",
            docs_url="/docs" if self.settings.get("ENVIRONMENT") == "development" else None,
            redoc_url="/redoc" if self.settings.get("ENVIRONMENT") == "development" else None,
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

        logger.info("✅ CogniForge ready to serve requests (النظام جاهز لاستقبال الطلبات)")

        yield  # النظام يعمل الآن هنا

        # === لحظة الإيقاف (SHUTDOWN) ===
        logger.info("👋 CogniForge shutting down... (جاري إيقاف النظام)")

    def _configure_middleware(self, app: FastAPI):
        """تجهيز طبقات الحماية والتحسين (Middleware Stack)."""

        # 1. المضيف الموثوق (Trusted Host): لمنع الهجمات من نطاقات غير معروفة.
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.settings.get("ALLOWED_HOSTS", [])
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

    def _discover_and_weave_blueprints(self):
        """
        يكتشف ويسجل كل المخططات (Blueprints) تلقائياً.
        يقوم هذا الكود بالبحث داخل مجلد `app/blueprints` عن أي ملف ينتهي بـ `_blueprint.py` ويقوم بتحميله.
        """
        blueprints_path = os.path.join(os.path.dirname(__file__), "blueprints")
        logger.info(f"Reality Kernel: Weaving blueprints from {blueprints_path}")

        # المشي عبر المجلدات (Walk)
        for _, _, files in os.walk(blueprints_path):
            for filename in files:
                if filename.endswith("_blueprint.py"):
                    self._load_blueprint_module(filename)

    def _load_blueprint_module(self, filename: str):
        """دالة مساعدة لتحميل ملف مخطط واحد."""
        module_name = f"app.blueprints.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            # فحص محتويات الملف للبحث عن كائن من نوع Blueprint
            for _, obj in inspect.getmembers(module):
                if isinstance(obj, Blueprint):
                    self._register_blueprint(obj)
        except ImportError as e:
            logger.error(f"Failed to import blueprint module {module_name}: {e}")

    def _register_blueprint(self, blueprint: Blueprint):
        """تسجيل المخطط في التطبيق الرئيسي."""
        logger.info(f"Weaving blueprint: {blueprint.name}")
        self.app.include_router(
            blueprint.router,
            prefix=f"/{blueprint.name}",
            tags=[blueprint.name.capitalize()]
        )
