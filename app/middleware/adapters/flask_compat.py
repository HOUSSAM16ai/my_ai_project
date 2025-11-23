from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.kernel_v2.compat_collapse import RequestContext, UserContext, AnonymousUser


class FlaskCompatMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with RequestContext(request):
            with UserContext(AnonymousUser()):
                response = await call_next(request)
                return response
