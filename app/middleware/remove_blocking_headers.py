from __future__ import annotations

import logging
from typing import Final

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# قائمة الترويسات المحظورة التي قد تكشف معلومات حساسة أو تعيق الأداء
# Blocked headers that might leak sensitive info or hinder performance
BLOCKED_HEADERS: Final[set[str]] = {
    "server",
    "x-powered-by",
    "x-aspnet-version",
    "x-runtime",
    # "keep-alive",  # REMOVED: Essential for SSE and persistent connections
}


class RemoveBlockingHeadersMiddleware(BaseHTTPMiddleware):
    """
    برمجية وسيطة لإزالة الترويسات غير المرغوب فيها (Sanitization Middleware).

    الأهداف:
    1. **إخفاء البصمة (Obscurity)**: إزالة ترويسات الخادم (`Server`, `X-Powered-By`) لتقليل سطح الهجوم.
    2. **تحسين الأداء (Performance)**: إزالة ترويسات قديمة قد تربك البروكسيات الحديثة.

    المعايير:
    - يعمل على كافة الردود الصادرة.
    - لا يؤثر على الترويسات الضرورية لـ SSE مثل `Cache-Control`.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # إزالة الترويسات المحظورة
        for header in BLOCKED_HEADERS:
            if header in response.headers:
                del response.headers[header]

        return response
