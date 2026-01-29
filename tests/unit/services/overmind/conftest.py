from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(autouse=True)
def init_db() -> None:
    """تعطيل تهيئة قاعدة البيانات لاختبارات هذا النطاق."""
    return


@pytest.fixture(autouse=True)
def clean_db() -> None:
    """تعطيل تنظيف قاعدة البيانات لاختبارات هذا النطاق."""
    return


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    """حلقة asyncio مخصصة لاختبارات هذا النطاق دون الاعتماد على القاعدة."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()
