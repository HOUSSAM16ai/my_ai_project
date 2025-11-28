import os
import logging

logger = logging.getLogger(__name__)

class RemoveBlockingHeadersMiddleware:
    """
    Pure ASGI Middleware to remove or relax headers that block iframe usage
    in GitHub Codespaces or Development environments.

    It strips 'X-Frame-Options' and removes 'frame-ancestors' from 'Content-Security-Policy'.
    """
    def __init__(self, app):
        self.app = app
        self.enabled = self._should_enable()
        if self.enabled:
            logger.warning("⚠️ RemoveBlockingHeadersMiddleware ENABLED. Security headers are relaxed for development.")

    def _should_enable(self) -> bool:
        # 1. GitHub Codespaces detection
        if os.getenv("CODESPACE_NAME"):
            return True
        # 2. Explicit Dev Environment
        if os.getenv("ENVIRONMENT", "").lower() == "development":
            return True
        return False

    async def __call__(self, scope, receive, send):
        if not self.enabled or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                new_headers = []
                for key, value in headers:
                    key_lower = key.decode("latin-1").lower()

                    # 1. Remove X-Frame-Options entirely
                    if key_lower == "x-frame-options":
                        continue

                    # 2. Relax Content-Security-Policy
                    if key_lower == "content-security-policy":
                        try:
                            val_str = value.decode("latin-1")
                            # Split by semicolon, filter out frame-ancestors
                            directives = [d.strip() for d in val_str.split(";") if d.strip()]
                            safe_directives = [d for d in directives if not d.lower().startswith("frame-ancestors")]

                            if safe_directives:
                                new_val = "; ".join(safe_directives)
                                new_headers.append((key, new_val.encode("latin-1")))
                            # If no directives left, we skip adding the header
                        except Exception:
                            # In case of decoding error, leave it as is (safer fallback)
                            new_headers.append((key, value))
                        continue

                    # Keep other headers
                    new_headers.append((key, value))

                message["headers"] = new_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
