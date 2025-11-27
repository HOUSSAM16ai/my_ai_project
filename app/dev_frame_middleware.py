import os
import re

from starlette.middleware.base import BaseHTTPMiddleware


class DevAllowIframeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        if os.environ.get("ENVIRONMENT", "") == "development":
            # Remove header that blocks framing
            if "x-frame-options" in response.headers:
                del response.headers["x-frame-options"]

            # Adjust CSP to allow display within an iframe in the development environment
            existing = response.headers.get("content-security-policy", "")
            if existing:
                if "frame-ancestors" in existing:
                    # Replace existing frame-ancestors directive with a permissive one
                    response.headers["content-security-policy"] = re.sub(
                        r"frame-ancestors[^;]+", "frame-ancestors *", existing
                    )
                else:
                    # Append it if not present
                    response.headers["content-security-policy"] = (
                        existing.rstrip(";") + "; frame-ancestors *;"
                    )
            else:
                response.headers["content-security-policy"] = "frame-ancestors *;"

        return response
