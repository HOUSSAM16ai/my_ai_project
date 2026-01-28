import pytest

from app.services.chat.tools.retrieval import remote_client


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _DummyAsyncClient:
    def __init__(self, payload):
        self._payload = payload
        self.last_request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        self.last_request = {"url": url, "json": json}
        return _DummyResponse(self._payload)


@pytest.mark.asyncio
async def test_fetch_from_memory_agent_filters_non_dict_results(monkeypatch):
    client = _DummyAsyncClient([{"id": 1}, "bad"])
    monkeypatch.setattr(remote_client.httpx, "AsyncClient", lambda timeout: client)

    results = await remote_client.fetch_from_memory_agent("query", tags=["math"])

    assert results == [{"id": 1}]


@pytest.mark.asyncio
async def test_fetch_from_memory_agent_returns_empty_on_invalid_payload(monkeypatch):
    client = _DummyAsyncClient({"message": "invalid"})
    monkeypatch.setattr(remote_client.httpx, "AsyncClient", lambda timeout: client)

    results = await remote_client.fetch_from_memory_agent("query", tags=[])

    assert results == []
