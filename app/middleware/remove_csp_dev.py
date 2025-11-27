# app/middleware/remove_csp_dev.py
import os
from starlette.middleware.base import BaseHTTPMiddleware

def running_in_codespace() -> bool:
    # reliable heuristic: check env or common Codespaces variables
    if os.getenv("CODESPACE_NAME"): return True
    # fallback: dev environment indicator
    if os.getenv("ENVIRONMENT", "").lower() == "development": return True
    return False

class RemoveBlockingHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.enabled = running_in_codespace()

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if self.enabled:
            # remove or relax only headers that prevent iframes
            if "x-frame-options" in response.headers:
                del response.headers["x-frame-options"]

            # Remove only the frame-ancestors directive if present
            if "content-security-policy" in response.headers:
                csp = response.headers["content-security-policy"]
                # remove frame-ancestors directive safely
                parts = [p.strip() for p in csp.split(";") if p.strip()]
                parts = [p for p in parts if not p.lower().startswith("frame-ancestors")]

                if parts:
                    response.headers["content-security-policy"] = "; ".join(parts)
                else:
                    del response.headers["content-security-policy"]
        return response
