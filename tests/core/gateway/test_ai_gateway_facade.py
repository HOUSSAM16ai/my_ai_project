import pytest

from app.core import ai_gateway as gateway_module
from app.core.gateway.simple_client import SimpleResponse


class _StubClient:
    def __init__(self):
        self.calls = []

    async def generate_text(self, prompt: str, **kwargs):
        self.calls.append(("generate_text", prompt, kwargs))
        return SimpleResponse(content="ok")

    async def forge_new_code(self, **kwargs):
        self.calls.append(("forge_new_code", "", kwargs))
        return SimpleResponse(content="code")

    def echo(self, value):
        return value


@pytest.mark.asyncio
async def test_ai_gateway_facade_uses_stub_client(monkeypatch):
    stub = _StubClient()
    monkeypatch.setattr(gateway_module, "get_ai_client", lambda: stub)
    facade = gateway_module.AIGatewayFacade()

    response = await facade.generate_text("hello", temperature=0.1)
    code_response = await facade.forge_new_code(prompt="hi")

    assert response.content == "ok"
    assert code_response.content == "code"
    assert stub.calls[0][0] == "generate_text"
    assert stub.calls[1][0] == "forge_new_code"


def test_ai_gateway_facade_delegates_attributes(monkeypatch):
    stub = _StubClient()
    monkeypatch.setattr(gateway_module, "get_ai_client", lambda: stub)
    facade = gateway_module.AIGatewayFacade()

    assert facade.echo("value") == "value"
