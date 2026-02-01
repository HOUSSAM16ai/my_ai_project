from unittest.mock import AsyncMock

import pytest

from app.core.event_bus_impl import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest.mark.asyncio
async def test_subscribe_publish(bus):
    mock_handler = AsyncMock()
    bus.subscribe("user.created", mock_handler)

    event = await bus.publish("user.created", {"id": 1}, "test")

    assert event.event_type == "user.created"
    mock_handler.assert_called_once()
    called_event = mock_handler.call_args[0][0]
    assert called_event.payload == {"id": 1}


@pytest.mark.asyncio
async def test_decorator_syntax(bus):
    received = []

    @bus.subscribe("order.placed")
    async def handler(event):
        received.append(event)

    await bus.publish("order.placed", {}, "test")
    assert len(received) == 1


@pytest.mark.asyncio
async def test_history_management(bus):
    await bus.publish("type1", {}, "s")
    await bus.publish("type1", {}, "s")
    await bus.publish("type2", {}, "s")

    events = bus.get_history("type1")
    assert len(events) == 2

    all_events = bus.get_history()
    assert len(all_events) == 3

    bus.clear_history()
    assert len(bus.get_history()) == 0


@pytest.mark.asyncio
async def test_unsubscribe(bus):
    mock = AsyncMock()
    bus.subscribe("topic", mock)
    bus.unsubscribe("topic", mock)

    await bus.publish("topic", {}, "s")
    mock.assert_not_called()
