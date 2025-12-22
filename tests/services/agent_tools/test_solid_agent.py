"""
Tests for the new SOLID Agent Architecture.
"""
import pytest
from app.services.agent_tools.domain.tool import StandardTool
from app.services.agent_tools.infrastructure.registry import InMemoryToolRegistry
from app.services.agent_tools.new_core import tool
from app.services.agent_tools.infrastructure.registry import get_registry

@pytest.mark.asyncio
async def test_tool_domain_execution():
    """Test that the StandardTool executes correctly."""
    async def sample_handler(x: int):
        return x * 2

    t = StandardTool(
        name="double",
        description="Doubles a number",
        parameters={"type": "object"},
        handler=sample_handler
    )

    result = await t.execute(x=5)
    assert result == 10
    assert t.name == "double"

@pytest.mark.asyncio
async def test_registry_operations():
    """Test the InMemoryToolRegistry."""
    registry = InMemoryToolRegistry()

    async def noop(): pass

    t = StandardTool("noop", "Does nothing", {}, noop)
    registry.register(t)

    assert registry.get("noop") == t
    assert registry.get("missing") is None
    assert len(registry.list_tools()) == 1

@pytest.mark.asyncio
async def test_decorator_registration():
    """Test that the @tool decorator registers tools correctly."""
    # Reset registry for test isolation (since it's a global singleton in the current simplistic impl)
    # Ideally, we should mock get_registry, but for this integration test, we check side effects.

    registry = get_registry()
    initial_count = len(registry.list_tools())

    @tool(name="test_tool_dec", description="Test Decorator")
    async def my_tool(a: str):
        return f"Hello {a}"

    # Check registration
    t = registry.get("test_tool_dec")
    assert t is not None
    assert t.description == "Test Decorator"

    # Check execution wrapper
    result = await my_tool(a="World")
    assert result == "Hello World"
