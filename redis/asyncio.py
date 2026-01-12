"""
تنفيذ مبسط لمكتبة redis.asyncio للاستخدام في بيئات الاختبار.
"""

from __future__ import annotations

from typing import AsyncIterator


class RedisStub:
    """عميل Redis وهمي بواجهات غير متزامنة."""

    async def get(self, key: str):
        return None

    async def set(self, key: str, value: str, ex: int | None = None):
        return True

    async def delete(self, key: str):
        return 0

    async def exists(self, key: str):
        return 0

    async def flushdb(self):
        return True

    async def scan_iter(self, match: str | None = None) -> AsyncIterator[str]:
        if False:
            yield match  # pragma: no cover


def from_url(*args, **kwargs) -> RedisStub:
    """يعيد عميل Redis وهمي."""
    return RedisStub()
