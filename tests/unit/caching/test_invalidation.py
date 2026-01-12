"""
اختبارات مدير الإبطال.
"""

from unittest.mock import AsyncMock

import pytest

from app.caching.base import CacheBackend
from app.caching.invalidation import InvalidationManager


@pytest.fixture
def backend_mock():
    return AsyncMock(spec=CacheBackend)


@pytest.fixture
def manager(backend_mock):
    return InvalidationManager(backend_mock)


@pytest.mark.asyncio
async def test_invalidate_pattern(manager, backend_mock):
    """اختبار إبطال النمط."""
    # Mock finding 2 keys
    backend_mock.scan_keys.return_value = ["user:1:profile", "user:1:settings"]
    backend_mock.delete.return_value = True

    count = await manager.invalidate_pattern("user:1:*")

    assert count == 2
    backend_mock.scan_keys.assert_awaited_once_with("user:1:*")
    # تأكد من حذف كل مفتاح
    assert backend_mock.delete.await_count == 2


@pytest.mark.asyncio
async def test_invalidate_user_cache(manager, backend_mock):
    """اختبار مساعد إبطال المستخدم."""
    backend_mock.scan_keys.return_value = ["user:99:a"]
    backend_mock.delete.return_value = True

    await manager.invalidate_user_cache("99")

    backend_mock.scan_keys.assert_awaited_once_with("user:99:*")
