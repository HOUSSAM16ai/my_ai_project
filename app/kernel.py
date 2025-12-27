"""
نواة الواقع الإدراكي (Reality Kernel).

هذا الملف يمثل القلب النابض للنظام (The Beating Heart) ومُنفذ (Evaluator) التطبيق.
يعتمد منهجية SICP (جامعة بيركلي) في التركيب الوظيفي (Functional Composition) وفصل التجريد.

المعايير المطبقة (Standards Applied):
- SICP: حواجز التجريد (Abstraction Barriers)، البيانات ككود (Code as Data).
- CS50 2025: صرامة النوع والتوثيق (Type Strictness & Documentation).
- SOLID: مبادئ التصميم القوي (Robust Design).
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Final

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# الموجهات محذوفة - سيتم استخدام API البسيط
from app.config.settings import AppSettings
from app.core.db_schema import validate_schema_on_startup
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

__all__ = ["RealityKernel"]

# ==============================================================================
# SICP: Data Abstraction (تجريد البيانات)
# ==============================================================================

# تعريف نوع MiddlewareSpec: (الفئة، المعاملات)
type MiddlewareSpec = tuple[type[BaseHTTPMiddleware] | type[ASGIApp] | Any, dict[str, Any]]

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
        # ملاحظة: RateLimitMiddleware يجب أن يُضاف بعناية حسب تصميمه (إذا كان BaseHTTPMiddleware)
        stack.insert(3, (RateLimitMiddleware, {}))

    return stack


def _get_router_registry() -> list[RouterSpec]:
    """
    سجل الموجهات (Router Registry) كبيانات.

    Returns:
        list[RouterSpec]: قائمة (الموجه، البادئة).
    """
    # الموجهات محذوفة - سيتم استخدام API البسيط من app.api.main
    return []


def _apply_middleware(app: FastAPI, stack: list[MiddlewareSpec]) -> FastAPI:
    """
    Combinator: تطبيق قائمة الميدل وير على التطبيق.

    هذا هو المعادل الوظيفي لحلقة تكرارية تقوم بـ 'add_middleware'.

    Args:
        app: تطبيق FastAPI.
        stack: قائمة مواصفات الميدل وير.

    Returns:
        FastAPI: التطبيق بعد التعديل.
    """
    for mw_cls, mw_options in reversed(stack): # FastAPI applies in reverse order of addition
        app.add_middleware(mw_cls, **mw_options)
    return app


def _mount_routers(app: FastAPI, registry: list[RouterSpec]) -> FastAPI:
    """
    Combinator: ربط الموجهات بالتطبيق.

    Args:
        app: تطبيق FastAPI.
        registry: سجل الموجهات.

    Returns:
        FastAPI: التطبيق بعد الربط.
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
    تطبيق دوال نقية على حالة النظام، بدلاً من احتوائها على منطق إجرائي معقد.
    """

    def __init__(self, *, settings: AppSettings | dict[str, Any]) -> None:
        """
        تهيئة النواة.

        Args:
            settings (AppSettings | dict[str, Any]): الإعدادات.
        """
        if isinstance(settings, dict):
            # Fail Fast: يجب أن يفشل التحقق فوراً إذا كانت الإعدادات غير صالحة
            self.settings_obj = AppSettings(**settings)
            self.settings_dict = self.settings_obj.model_dump()
        else:
            self.settings_obj = settings
            self.settings_dict = settings.model_dump()

        # The Functional Pipeline:
        # 1. Create Base App
        # 2. Get Specs (Data)
        # 3. Apply Transformations (Functions)

        self.app: Final[FastAPI] = self._construct_app()


    def get_app(self) -> FastAPI:
        """Returns the constructed application."""
        return self.app


    def _construct_app(self) -> FastAPI:
        """
        بناء التطبيق باستخدام منهجية Pipeline.
        """
        # 1. Base State
        app = self._create_base_app_instance()

        # 2. Data Acquisition (Pure)
        middleware_stack = (
            _get_middleware_stack(self.settings_obj) if self.settings_obj else []
        )
        router_registry = _get_router_registry()

        # 3. Transformations (Side-effects confined here)
        app = _apply_middleware(app, middleware_stack)
        add_error_handlers(app)  # Legacy helper, treated as a transformer
        return _mount_routers(app, router_registry)


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
            version=self.settings_dict.get("VERSION", "v4.1-SICP-Edition"),
            docs_url="/docs" if is_dev else None,
            redoc_url="/redoc" if is_dev else None,
            lifespan=lifespan,
        )


    async def _handle_lifespan_events(self) -> AsyncGenerator[None, None]:
        """
        معالجة أحداث النظام الحيوية.
        """
        logger.info("🚀 CogniForge System Initializing... (SICP Boot Sequence)")

        if self.settings_dict.get("ENVIRONMENT") != "testing":
            try:
                await validate_schema_on_startup()
                logger.info("✅ Database Schema Validated")
            except Exception as e:
                logger.warning(f"⚠️ Schema validation warning: {e}")

        logger.info("✅ System Ready")
        yield
        logger.info("👋 CogniForge System Shutting Down...")
