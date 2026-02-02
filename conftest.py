"""جسر إعدادات الاختبار لتعميم تجهيزات asyncio عبر جميع المسارات."""

from tests.conftest import *  # noqa: F403

import inspect

import httpx


def _patch_httpx_for_starlette() -> None:
    """يضبط httpx لقبول وسيط app عند إنشاء TestClient."""
    signature = inspect.signature(httpx.Client.__init__)
    if "app" in signature.parameters:
        return

    original_init = httpx.Client.__init__

    def _patched_init(self, *args, app=None, **kwargs):  # type: ignore[no-untyped-def]
        if app is not None and "transport" not in kwargs:
            kwargs["transport"] = httpx.ASGITransport(app=app)
            kwargs.setdefault("base_url", "http://testserver")
        original_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_init  # type: ignore[assignment]


_patch_httpx_for_starlette()
