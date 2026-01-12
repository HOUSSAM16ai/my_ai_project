# app/middleware/core/base_middleware.py
# ======================================================================================
# ==                    BASE MIDDLEWARE ABSTRACT CLASS (v∞)                         ==
# ======================================================================================
"""
الوسيط الأساسي - Base Middleware

طبقة تجريدية تجمع دورة حياة الوسيط وتوحّد طريقة التنفيذ لضمان الانسجام بين
الوحدات. يعتمد التصميم على «قالب المنهج» مع تركيز على الأجزاء القابلة
للتوسعة وتطبيق مبدأ القشرة الوظيفية مع الحد الأدنى من الآثار الجانبية.
"""

from abc import ABC, abstractmethod

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .context import RequestContext
from .result import MiddlewareResult


class BaseMiddleware(BaseHTTPMiddleware, ABC):
    """
    الطبقة التجريدية الرئيسية لجميع الوسطاء.

    تفرض هذه الطبقة واجهة موحّدة لمعالجة الطلبات وتقدم نقاط تمدد للحياة
    الكاملة للوسيط من التهيئة حتى إنهاء الطلب. توثيق السمات يسهّل على
    المبتدئين فهم دور كل وسيط وكيفية تخصيصه بأمان.

    السمات:
        name: اسم فريد للوسيط.
        order: ترتيب التنفيذ (الأصغر ينفذ أولاً).
        enabled: حالة التفعيل.
        config: إعدادات التكوين الخاصة بالوسيط.
    """

    # Class-level defaults (can be overridden)
    name: str = "BaseMiddleware"
    order: int = 0
    enabled: bool = True

    def __init__(self, app: ASGIApp, config: dict[str, object] | None = None):
        """يهيئ الوسيط مع إمكانية تمرير إعدادات تكوين اختيارية."""
        super().__init__(app)
        self.config = config or {}
        self._setup()

    def _setup(self) -> None:
        """إعداد داخلي يمكن للوسطاء المشتقة تخصيصه عند الحاجة."""

    @abstractmethod
    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """يعالج الطلب بشكل متزامن ويعيد نتيجة تصف حالة النجاح أو الفشل."""
        raise NotImplementedError

    async def process_request_async(self, ctx: RequestContext) -> MiddlewareResult:
        """ينفذ المعالجة غير المتزامنة مع الاعتماد على النسخة المتزامنة افتراضياً."""
        return self.process_request(ctx)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """واجهة الدمج مع Starlette/FastAPI لإدارة تدفق الطلبات."""
        if not self.enabled:
            return await call_next(request)

        ctx = await RequestContext.from_fastapi_request(request)

        if not self.should_process(ctx):
            return await call_next(request)

        try:
            result = await self.process_request_async(ctx)
        except Exception as exc:  # pragma: no cover - حراسة تنفيذية
            self.on_error(ctx, exc)
            raise

        if not result.is_success:
            self.on_error(ctx, ValueError(result.message))
            self.on_complete(ctx, result)

            return self._render_error_response(result)

        response = await call_next(request)

        self.on_success(ctx)
        self.on_complete(ctx, result)

        sec_headers = ctx.get_metadata("security_headers")
        if sec_headers and isinstance(sec_headers, dict):
            for header, value in sec_headers.items():
                response.headers[header] = value

        return response

    def _render_error_response(self, result: MiddlewareResult) -> JSONResponse:
        """يبني استجابة JSON موحدة لنتائج الفشل مع الحفاظ على التفاصيل."""

        status_code, content = result.to_response_components()
        if "details" not in content:
            content["details"] = result.details

        return JSONResponse(status_code=status_code, content=content)

    def on_success(self, ctx: RequestContext) -> None:
        """خطاف يُستدعى عند نجاح التحقق للوسيط، قابل للتخصيص."""

    def on_error(self, ctx: RequestContext, error: Exception) -> None:
        """خطاف يُستدعى عند حدوث خطأ أثناء تنفيذ الوسيط."""

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """خطاف يُستدعى بعد اكتمال التنفيذ لأي تنظيف أو قياس."""

    def should_process(self, ctx: RequestContext) -> bool:
        """يحدد ما إذا كان الوسيط يجب أن يعمل على الطلب الحالي."""
        return self.enabled

    def get_statistics(self) -> dict[str, object]:
        """يعيد بيانات القياس التراكمية للوسيط."""
        return {
            "name": self.name,
            "order": self.order,
            "enabled": self.enabled,
        }

    def __repr__(self) -> str:
        """تمثيل نصي مهيأ لأغراض التشخيص."""
        return f"{self.__class__.__name__}(name={self.name}, order={self.order})"


class ConditionalMiddleware(BaseMiddleware):
    """قاعدة لوسطاء يعتمد تشغيلهم على شروط المسار أو الطريقة."""

    def __init__(self, app: ASGIApp, config: dict[str, object] | None = None):
        super().__init__(app, config)
        self.include_paths: list[str] = self.config.get("include_paths", [])
        self.exclude_paths: list[str] = self.config.get("exclude_paths", [])
        self.methods: list[str] = self.config.get("methods", [])

    def should_process(self, ctx: RequestContext) -> bool:
        """يتحقق من مطابقة الطلب للشروط المحددة قبل المعالجة."""
        if not super().should_process(ctx):
            return False

        # Check excluded paths first
        if self.exclude_paths:
            for path in self.exclude_paths:
                if ctx.path.startswith(path):
                    return False

        # Check included paths
        if self.include_paths:
            matches = False
            for path in self.include_paths:
                if ctx.path.startswith(path):
                    matches = True
                    break
            if not matches:
                return False

        # Check HTTP methods
        return not (self.methods and ctx.method not in self.methods)


class MetricsMiddleware(BaseMiddleware):
    """قاعدة لوسطاء جمع المقاييس ومراقبة معدلات النجاح والفشل."""

    def __init__(self, app: ASGIApp, config: dict[str, object] | None = None):
        super().__init__(app, config)
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0

    def on_success(self, ctx: RequestContext) -> None:
        self.success_count += 1
        self.request_count += 1

    def on_error(self, ctx: RequestContext, error: Exception) -> None:
        self.failure_count += 1
        self.request_count += 1

    def get_statistics(self) -> dict[str, object]:
        stats = super().get_statistics()
        stats.update(
            {
                "request_count": self.request_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": (
                    self.success_count / self.request_count if self.request_count > 0 else 0.0
                ),
            }
        )
        return stats
