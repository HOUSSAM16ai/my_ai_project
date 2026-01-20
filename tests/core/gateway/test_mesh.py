
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import httpx
# Import mesh module but we will patch attributes on it
import app.core.gateway.mesh as mesh_module
from app.core.gateway.mesh import NeuralRoutingMesh
from app.core.gateway.circuit_breaker import CircuitState
from app.core.gateway.node import NeuralNode

# Helper to mock async iterator
class AsyncIterator:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        self.iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

@pytest.fixture
def setup_mocks():
    # Patch the global constants/config in the module
    with patch.object(mesh_module, "PRIMARY_MODEL", "primary-model"), \
         patch.object(mesh_module, "FALLBACK_MODELS", ["backup-model-1", "backup-model-2"]), \
         patch.object(mesh_module, "SAFETY_NET_MODEL_ID", "system/safety-net"), \
         patch("app.core.gateway.mesh.get_cognitive_engine") as mock_cog:

        mock_cog.return_value.recall.return_value = None
        yield

@pytest.fixture
def mock_httpx_client():
    with patch("app.core.gateway.connection.ConnectionManager.get_client") as mock:
        client = AsyncMock(spec=httpx.AsyncClient)
        mock.return_value = client
        yield client

@pytest.mark.asyncio
async def test_initialization(setup_mocks):
    mesh = NeuralRoutingMesh("test-key")
    nodes = mesh.nodes_map

    assert "primary-model" in nodes
    assert "backup-model-1" in nodes
    assert "backup-model-2" in nodes
    assert "system/safety-net" in nodes

    assert nodes["primary-model"].model_id == "primary-model"

@pytest.mark.asyncio
async def test_prioritization(setup_mocks):
    mesh = NeuralRoutingMesh("test-key")
    # Updated to use manager
    nodes = mesh.manager.get_prioritized_nodes("test prompt")
    model_ids = [n.model_id for n in nodes]
    assert model_ids == ["primary-model", "backup-model-1", "backup-model-2", "system/safety-net"]

@pytest.mark.asyncio
async def test_prioritization_with_circuit_open(setup_mocks):
    mesh = NeuralRoutingMesh("test-key")

    # Simulate primary failure
    mesh.nodes_map["primary-model"].circuit_breaker.state = CircuitState.OPEN
    mesh.nodes_map["primary-model"].circuit_breaker.last_failure_time = 9999999999 # Future

    # Updated to use manager
    nodes = mesh.manager.get_prioritized_nodes("test prompt")
    model_ids = [n.model_id for n in nodes]

    assert "primary-model" not in model_ids
    assert model_ids[0] == "backup-model-1"

@pytest.mark.asyncio
async def test_stream_chat_success_primary(setup_mocks, mock_httpx_client):
    mesh = NeuralRoutingMesh("test-key")

    # Mock successful streaming response
    mock_response = MagicMock()
    mock_response.status_code = 200

    lines = [
        "data: " + json.dumps({"choices": [{"delta": {"content": "Hello"}}], "model": "primary-model"}),
        "data: " + json.dumps({"choices": [{"delta": {"content": " World"}}], "model": "primary-model"}),
        "data: [DONE]"
    ]
    mock_response.aiter_lines.return_value = AsyncIterator(lines)

    # Setup context manager for client.stream
    mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response

    messages = [{"role": "user", "content": "Hello"}]
    chunks = []
    async for chunk in mesh.stream_chat(messages):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert chunks[1]["choices"][0]["delta"]["content"] == " World"

@pytest.mark.asyncio
async def test_stream_chat_failover(setup_mocks):
    mesh = NeuralRoutingMesh("test-key")

    async def exec_side_effect(client, node, msgs):
        if node.model_id == "primary-model":
            raise httpx.ConnectError("Failed")
        if node.model_id == "backup-model-1":
            yield {"choices": [{"delta": {"content": "Backup"}}]}

    with patch.object(mesh.processor, "_execute_request", side_effect=exec_side_effect):
        messages = [{"role": "user", "content": "Hello"}]
        chunks = []
        async for chunk in mesh.stream_chat(messages):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0]["choices"][0]["delta"]["content"] == "Backup"
        assert mesh.nodes_map["primary-model"].circuit_breaker.failure_count == 1

@pytest.mark.asyncio
async def test_safety_net_activation(setup_mocks):
    mesh = NeuralRoutingMesh("test-key")

    # Force all regular nodes to be open/failed
    for nid, node in mesh.nodes_map.items():
        if nid != "system/safety-net":
            node.circuit_breaker.state = CircuitState.OPEN
            node.circuit_breaker.last_failure_time = 9999999999

    messages = [{"role": "user", "content": "Hello"}]
    chunks = []

    async for chunk in mesh.stream_chat(messages):
        chunks.append(chunk)

    assert len(chunks) > 0
    content = "".join([c["choices"][0]["delta"]["content"] for c in chunks])
    assert "System Alert" in content
