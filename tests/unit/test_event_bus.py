import asyncio

import pytest

from app.core import event_bus


@pytest.fixture(autouse=True)
def init_db() -> None:
    """تعطيل تهيئة قاعدة البيانات لهذه الوحدة."""


@pytest.fixture(autouse=True)
def clean_db() -> None:
    """تعطيل تنظيف قاعدة البيانات لهذه الوحدة."""
    yield


@pytest.mark.asyncio
async def test_publish_delivers_to_queue_subscribers() -> None:
    bus = event_bus.EventBus()
    queue = bus.subscribe_queue("channel")

    await bus.publish("channel", {"payload": 1})

    assert await queue.get() == {"payload": 1}


@pytest.mark.asyncio
async def test_publish_ignores_missing_subscribers() -> None:
    bus = event_bus.EventBus()

    await bus.publish("missing", "event")

    assert bus._subscribers == {}


@pytest.mark.asyncio
async def test_subscribe_generator_unregisters_on_close() -> None:
    bus = event_bus.EventBus()

    stream = bus.subscribe("updates")
    task = asyncio.create_task(anext(stream))
    await asyncio.sleep(0)

    await bus.publish("updates", "ready")

    assert await asyncio.wait_for(task, timeout=1) == "ready"

    await asyncio.wait_for(stream.aclose(), timeout=1)

    assert "updates" not in bus._subscribers


def test_get_event_bus_returns_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(event_bus, "_global_event_bus", None)

    first = event_bus.get_event_bus()
    second = event_bus.get_event_bus()

    assert first is second
