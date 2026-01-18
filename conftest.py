"""يهيئ تنفيذ الدوال غير المتزامنة في pytest دون اعتماد خارجي."""

from __future__ import annotations

import asyncio
import inspect

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """يشغل الدوال غير المتزامنة عبر حلقة asyncio محلية عند الحاجة."""
    test_func = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_func):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            signature = inspect.signature(test_func)
            kwargs = {
                name: pyfuncitem.funcargs[name]
                for name in signature.parameters
                if name in pyfuncitem.funcargs
            }
            loop.run_until_complete(test_func(**kwargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
