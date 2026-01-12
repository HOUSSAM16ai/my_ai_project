from __future__ import annotations

import logging
import os
from typing import Final

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# قائمة الترويسات المحظورة التي قد تكشف معلومات حساسة أو تعيق الأداء
# Blocked headers that might leak sensitive info or hinder performance
ALWAYS_BLOCKED_HEADERS: Final[set[str]] = {
    "server",
    "x-powered-by",
    "x-aspnet-version",
    "x-runtime",
    # "keep-alive",  # REMOVED: Essential for SSE and persistent connections
}

# ترويسات حماية الواجهات التي يتم تخفيفها فقط في بيئات المعاينة والتطوير
PREVIEW_ONLY_HEADERS: Final[set[str]] = {
    "x-frame-options",
}


class RemoveBlockingHeadersMiddleware(BaseHTTPMiddleware):
    """
    برمجية وسيطة لإزالة الترويسات غير المرغوب فيها (Sanitization Middleware).

    الأهداف:
    1. **إخفاء البصمة (Obscurity)**: إزالة ترويسات الخادم (`Server`, `X-Powered-By`) لتقليل سطح الهجوم دائماً.
    2. **تحسين تجربة المعاينة (Preview/Dev)**: تخفيف سياسات الإطار (X-Frame-Options و frame-ancestors) في بيئات التطوير أو Codespaces فقط.

    السمات:
        enabled: يحدد ما إذا كان تخفيف ترويسات الحماية مفعّلاً (بيئات التطوير والمعاينة).
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        environment: str | None = None,
        codespace_name: str | None = None,
        codespaces: str | None = None,
    ) -> None:
        """تهيئة الوسيط مع اكتشاف تلقائي للبيئة الحالية.

        Args:
            app: تطبيق ASGI المستهدف.
            environment: قيمة مخصصة لـ ENVIRONMENT (مفيدة للاختبارات).
            codespace_name: قيمة مخصصة لـ CODESPACE_NAME (مفيدة للاختبارات).
            codespaces: قيمة مخصصة لـ CODESPACES (مفيدة للاختبارات).
        """
        super().__init__(app)
        self._environment = (environment or os.environ.get("ENVIRONMENT", "")).lower()
        self._codespace_name = codespace_name or os.environ.get("CODESPACE_NAME")
        self._codespaces = codespaces or os.environ.get("CODESPACES")
        self.enabled = self._should_enable_preview_headers()

    def _should_enable_preview_headers(self) -> bool:
        """تحديد ما إذا كان يجب تخفيف ترويسات الحماية للمعاينة.

        يتم التخفيف فقط عند العمل داخل بيئات معاينة صريحة مثل Codespaces أو عند
        ضبط البيئة على "preview"؛ بيئة التطوير العادية تحتفظ بالترويسات الوقائية.
        """
        env = self._environment

        if self._codespace_name or self._codespaces:
            return True

        if env == "preview":
            return True

        if env == "development":
            return not hasattr(self.app, "router")

        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """معالجة الطلب وإزالة الترويسات وفقاً للبيئة."""
        response = await call_next(request)
        self._remove_always_blocked_headers(response)

        relax_headers = self.enabled
        if self._environment == "development" and hasattr(self.app, "router"):
            relax_headers = False
        request_app = request.scope.get("app")
        if self._environment == "development" and isinstance(request_app, Starlette):
            relax_headers = False

        if relax_headers:
            self._relax_preview_headers(response)

        return response

    def _remove_always_blocked_headers(self, response: Response) -> None:
        """إزالة الترويسات الممنوعة دائماً مثل Server وX-Powered-By."""
        for header in ALWAYS_BLOCKED_HEADERS:
            if header in response.headers:
                del response.headers[header]

    def _relax_preview_headers(self, response: Response) -> None:
        """تخفيف القيود الخاصة بالمعاينة (X-Frame-Options و frame-ancestors)."""
        for header in PREVIEW_ONLY_HEADERS:
            if header in response.headers:
                del response.headers[header]

        csp = response.headers.get("content-security-policy")
        if csp:
            cleaned_csp = self._strip_frame_ancestors(csp)
            if cleaned_csp:
                response.headers["content-security-policy"] = cleaned_csp
            else:
                del response.headers["content-security-policy"]

    @staticmethod
    def _strip_frame_ancestors(policy: str) -> str:
        """إزالة توجيه frame-ancestors مع الحفاظ على بقية سياسة CSP."""
        directives = [segment.strip() for segment in policy.split(";")]
        preserved = [d for d in directives if d and not d.lower().startswith("frame-ancestors")]
        return "; ".join(preserved)
