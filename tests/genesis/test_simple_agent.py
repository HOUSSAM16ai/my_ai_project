"""
Test Suite for Genesis Agent.
Verifies the simplicity protocol without external calls.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.genesis.core import GenesisAgent
from app.genesis.brain import Cortex

class MockMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

class MockToolCall:
    def __init__(self, id, name, args):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = args

@pytest.fixture
def mock_cortex():
    with patch("app.genesis.core.Cortex") as MockCortex:
        instance = MockCortex.return_value
        yield instance

def test_genesis_simple_reply(mock_cortex):
    """Test that agent returns direct answers."""
    # Setup
    agent = GenesisAgent()
    mock_cortex.think.return_value = MockMessage(content="Hello World")

    # Run
    response = agent.run("Hi")

    # Verify
    assert response == "Hello World"
    assert len(agent.memory.messages) == 2  # User + Assistant

def test_genesis_tool_usage(mock_cortex):
    """Test the Think -> Act -> Observe loop."""
    agent = GenesisAgent()

    # Mock Tool
    def magic_number() -> str:
        """Returns 42."""
        return "42"
    agent.register_tool(magic_number)

    # Mock LLM Responses
    # 1. First call: Request Tool
    tool_call = MockToolCall("call_1", "magic_number", "{}")
    msg_1 = MockMessage(content=None, tool_calls=[tool_call])

    # 2. Second call: Final Answer
    msg_2 = MockMessage(content="The number is 42")

    mock_cortex.think.side_effect = [msg_1, msg_2]

    # Run
    response = agent.run("What is the magic number?")

    # Verify
    assert response == "The number is 42"
    assert len(agent.memory.messages) > 2
    # Verify tool was actually executed
    # We can check memory for the tool result
    tool_msgs = [m for m in agent.memory.messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["content"] == "42"
