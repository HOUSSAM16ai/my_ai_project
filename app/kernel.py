"""
نواة الواقع الإدراكي (Reality Kernel) - 100% API-First.

هذا الملف يمثل القلب النابض للنظام (The Beating Heart) ومُنفذ (Evaluator) التطبيق.
يعتمد منهجية SICP (جامعة بيركلي) في التركيب الوظيفي (Functional Composition) وفصل التجريد.

المبدأ الأساسي: API-First Architecture
- النواة تركز 100% على API endpoints
- Frontend (static files) اختياري ومنفصل تماماً
- يمكن تشغيل النظام بدون frontend (API-only mode)
- Separation of Concerns: API Core لا يعرف شيئاً عن UI

المعايير المطبقة (Standards Applied):
- SICP: حواجز التجريد (Abstraction Barriers)، البيانات ككود (Code as Data).
- CS50 2025: صرامة النوع والتوثيق (Type Strictness & Documentation).
- SOLID: مبادئ التصميم القوي (Robust Design).
- API-First: النظام يعمل بشكل مستقل عن UI.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Final

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# استيراد الموجهات بشكل صريح
from app.api.routers import admin, crud, customer_chat, data_mesh, observability, overmind, security, system
from app.api.routers import ums
from app.config.settings import AppSettings
from app.core.db_schema import validate_schema_on_startup
from app.core.database import async_session_factory
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware
from app.middleware.static_files_middleware import StaticFilesConfig, setup_static_files_middleware
from app.services.bootstrap import bootstrap_admin_account

logger = logging.getLogger(__name__)

__all__ = ["RealityKernel"]

# ==============================================================================
# SICP: Data Abstraction (تجريد البيانات)
# ==============================================================================

# تعريف نوع MiddlewareSpec: (الفئة، المعاملات)
# يدعم أي middleware متوافق مع BaseHTTPMiddleware أو ASGIApp
type MiddlewareSpec = tuple[type[BaseHTTPMiddleware] | type, dict[str, object]]

# تعريف نوع RouterSpec: (الموجه، البادئة)
type RouterSpec = tuple[APIRouter, str]

# ==============================================================================
# SICP: Functional Core (الجوهر الوظيفي)
# ==============================================================================

def _get_middleware_stack(settings: AppSettings) -> list[MiddlewareSpec]:
    """
    تكوين قائمة البرمجيات الوسيطة كبيانات وصفية (Declarative Data).

    بدلاً من استدعاء الدوال بشكل إجرائي، نُعرف "ماذا نريد" كقائمة بيانات.

    Args:
        settings: إعدادات التطبيق.

    Returns:
        list[MiddlewareSpec]: قائمة المواصفات.
    """
    # تجهيز إعدادات CORS
    raw_origins = settings.BACKEND_CORS_ORIGINS
    allow_origins = raw_origins if raw_origins else ["*"]  # Fallback

    # تجهيز المكدس (الترتيب مهم: من الخارج إلى الداخل)
    stack: list[MiddlewareSpec] = [
        # 1. المضيف الموثوق (Trusted Host)
        (TrustedHostMiddleware, {"allowed_hosts": settings.ALLOWED_HOSTS}),

        # 2. CORS
        (CORSMiddleware, {
            "allow_origins": allow_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": ["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
            "expose_headers": ["Content-Length", "Content-Range"],
        }),

        # 3. ترويسات الأمان (Security Headers)
        (SecurityHeadersMiddleware, {}),

        # 4. تنظيف الترويسات (Clean Headers)
        (RemoveBlockingHeadersMiddleware, {}),

        # 5. ضغط البيانات (GZip)
        (GZipMiddleware, {"minimum_size": 1000}),
    ]

    # إضافة تحديد المعدل فقط في غير بيئة الاختبار
    if settings.ENVIRONMENT != "testing":
        stack.insert(3, (RateLimitMiddleware, {}))

    return stack

def _get_router_registry() -> list[RouterSpec]:
    """
    سجل الموجهات (Router Registry) كبيانات.

    Returns:
        list[RouterSpec]: قائمة (الموجه، البادئة).
    """
    return [
        (system.root_router, ""), # Root Level (e.g., /health)
        (system.router, ""),      # /system prefix is inside the router
        (admin.router, ""),
        (ums.router, ""),
        (security.router, "/api/security"),
        (data_mesh.router, "/api/v1/data-mesh"),
        (observability.router, "/api/observability"),
        (crud.router, "/api/v1"),
        (customer_chat.router, ""),
        (overmind.router, ""),
    ]

def _apply_middleware(app: FastAPI, stack: list[MiddlewareSpec]) -> FastAPI:
    """
    Combinator: تطبيق قائمة الميدل وير على التطبيق.
    """
    for mw_cls, mw_options in reversed(stack):
        app.add_middleware(mw_cls, **mw_options)
    return app

def _mount_routers(app: FastAPI, registry: list[RouterSpec]) -> FastAPI:
    """
    Combinator: ربط الموجهات بالتطبيق.
    """
    for router, prefix in registry:
        app.include_router(router, prefix=prefix)
    return app

# ==============================================================================
# The Evaluator (مُنفذ النظام)
# ==============================================================================

class RealityKernel:
    """
    نواة الواقع الإدراكي (Cognitive Reality Weaver).

    تعمل هذه الفئة الآن كـ "مُنسق" (Orchestrator) يقوم بتجميع التطبيق من خلال
    تطبيق دوال نقية على حالة النظام.
    """

    def __init__(
        self,
        *,
        settings: AppSettings | dict[str, object],
        enable_static_files: bool = True,
    ) -> None:
        """
        تهيئة النواة.

        Args:
            settings (AppSettings | dict[str, object]): الإعدادات.
            enable_static_files (bool): تفعيل خدمة الملفات الثابتة (افتراضي: True).
                                       يمكن تعطيله لوضع API-only.
        """
        if isinstance(settings, dict):
            self.settings_obj = AppSettings(**settings)
            self.settings_dict = self.settings_obj.model_dump()
        else:
            self.settings_obj = settings
            self.settings_dict = settings.model_dump()
        
        self.enable_static_files = enable_static_files

        # بناء التطبيق فور الإنشاء
        self.app: Final[FastAPI] = self._construct_app()

    def get_app(self) -> FastAPI:
        """Returns the constructed application."""
        return self.app

    def _construct_app(self) -> FastAPI:
        """
        بناء التطبيق باستخدام منهجية Pipeline.

        الخطوات:
        1. الحالة الأساسية (Base State)
        2. الحصول على المواصفات (Data Acquisition)
        3. تحويل الحالة (Transformations) - API Core فقط
        4. إعداد الواجهة الأمامية (Optional - منفصل عن API)
        """
        # 1. Base State
        app = self._create_base_app_instance()

        # 2. Data Acquisition (Pure)
        middleware_stack = (
            _get_middleware_stack(self.settings_obj) if self.settings_obj else []
        )
        router_registry = _get_router_registry()

        # 3. Transformations - API Core (100% API-First)
        app = _apply_middleware(app, middleware_stack)
        add_error_handlers(app)  # Legacy helper
        app = _mount_routers(app, router_registry)

        # 4. Static Files (Optional - Frontend Support)
        # Principle: API-First - يمكن تشغيل API بدون frontend
        # يتم الإعداد أخيراً لضمان عدم تداخل المسارات مع API
        if self.enable_static_files:
            static_config = StaticFilesConfig(
                enabled=True,
                serve_spa=True,
            )
            setup_static_files_middleware(app, static_config)
        else:
            logger.info("🚀 Running in API-only mode (no static files)")

        return app

    def _create_base_app_instance(self) -> FastAPI:
        """
        إنشاء مثيل FastAPI الخام مع مدير دورة الحياة.
        """
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
            """Lifecycle Manager Closure."""
            async for _ in self._handle_lifespan_events():
                yield

        is_dev: bool = self.settings_dict.get("ENVIRONMENT") == "development"

        return FastAPI(
            title=self.settings_dict.get("PROJECT_NAME", "CogniForge"),
            version=self.settings_dict.get("VERSION", "v4.2-Strict-Core"),
            docs_url="/docs" if is_dev else None,
            redoc_url="/redoc" if is_dev else None,
            lifespan=lifespan,
        )

    async def _handle_lifespan_events(self) -> AsyncGenerator[None, None]:
        """
        معالجة أحداث النظام الحيوية.
        """
        logger.info("🚀 CogniForge System Initializing... (Strict Mode Active)")

        try:
            await validate_schema_on_startup()
            logger.info("✅ Database Schema Validated")
        except Exception as e:
            logger.warning(f"⚠️ Schema validation warning: {e}")

        try:
            async with async_session_factory() as session:
                await bootstrap_admin_account(session, settings=self.settings_obj)
                logger.info("✅ Admin account bootstrapped and validated")
        except Exception as exc:
            logger.error(f"❌ Failed to bootstrap admin account: {exc}")

        logger.info("✅ System Ready")
        yield
        logger.info("👋 CogniForge System Shutting Down...")
