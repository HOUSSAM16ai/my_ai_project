from typing import Protocol

import pytest

from app.core.registry.plugin_registry import PluginRegistry


# Mock Plugin Protocol
class MockPlugin(Protocol):
    name: str
    plugin_type: str


class ConcretePlugin:
    def __init__(self, name, ptype="test"):
        self.name = name
        self.plugin_type = ptype


def test_singleton_behavior():
    r1 = PluginRegistry()
    r2 = PluginRegistry()
    assert r1 is r2


def test_register_get_unregister():
    reg = PluginRegistry()
    reg.clear()  # Reset for test

    p = ConcretePlugin("plugin-1")
    reg.register(p, metadata={"version": "1.0"})

    assert reg.get("plugin-1") is p
    assert reg.get_metadata("plugin-1") == {"version": "1.0"}

    # Duplicate
    with pytest.raises(ValueError):
        reg.register(p)

    assert reg.unregister("plugin-1") is True
    assert reg.get("plugin-1") is None
    assert reg.unregister("missing") is False


def test_get_by_type():
    reg = PluginRegistry()
    reg.clear()

    p1 = ConcretePlugin("p1", "type-a")
    p2 = ConcretePlugin("p2", "type-b")
    p3 = ConcretePlugin("p3", "type-a")

    reg.register(p1)
    reg.register(p2)
    reg.register(p3)

    results = reg.get_by_type("type-a")
    assert len(results) == 2
    assert p1 in results
    assert p3 in results
