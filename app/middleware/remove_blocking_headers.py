# app/middleware/remove_blocking_headers.py
import logging
import os

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("remove_blocking_headers")
logger.setLevel(logging.INFO)

def running_in_dev_or_codespace() -> bool:
    # Detect Codespaces or explicit development
    if os.getenv("CODESPACES") == "true" or os.getenv("CODESPACE_NAME"):
        return True
    return os.getenv("ENVIRONMENT", "").lower() == "development"

class RemoveBlockingHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.enabled = running_in_dev_or_codespace()
        logger.info(f"RemoveBlockingHeadersMiddleware enabled={self.enabled}")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                # Remove X-Frame-Options entirely
                if "x-frame-options" in headers:
                    try:
                        del headers["x-frame-options"]
                    except Exception:
                        headers.pop("x-frame-options", None)
                # Adjust CSP: remove frame-ancestors directive only
                csp = headers.get("content-security-policy")
                if csp:
                    parts = [p.strip() for p in csp.split(";") if p.strip()]
                    parts = [p for p in parts if not p.lower().startswith("frame-ancestors")]
                    if parts:
                        headers["content-security-policy"] = "; ".join(parts)
                    else:
                        # remove CSP entirely if only frame-ancestors existed
                        try:
                            del headers["content-security-policy"]
                        except Exception:
                            headers.pop("content-security-policy", None)
            await send(message)

        await self.app(scope, receive, send_wrapper)
