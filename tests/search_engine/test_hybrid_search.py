import pytest

from app.services.search_engine import hybrid


class _DummyEmbedding:
    def get_text_embedding(self, query):
        return [0.1]


class _DummyRow:
    def __init__(self, mapping):
        self._mapping = mapping


class _DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _DummySession:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt, params):
        return _DummyResult(self._rows)


class _DummySessionContext:
    def __init__(self, rows):
        self._rows = rows

    async def __aenter__(self):
        return _DummySession(self._rows)

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_hybrid_search_returns_empty_for_no_candidates(monkeypatch):
    monkeypatch.setattr(hybrid, "get_embedding_model", lambda: _DummyEmbedding())
    monkeypatch.setattr(hybrid, "async_session_factory", lambda: _DummySessionContext([]))

    results = await hybrid.hybrid_search("query", top_k=3)

    assert results == []


@pytest.mark.asyncio
async def test_hybrid_search_falls_back_when_reranker_fails(monkeypatch):
    rows = [
        _DummyRow(
            {
                "id": "a",
                "label": "A",
                "name": "Alpha",
                "content": "First",
                "dense_score": 0.9,
                "sparse_score": 0.1,
            }
        ),
        _DummyRow(
            {
                "id": "b",
                "label": "B",
                "name": "Beta",
                "content": "Second",
                "dense_score": 0.5,
                "sparse_score": 1.0,
            }
        ),
    ]

    monkeypatch.setattr(hybrid, "get_embedding_model", lambda: _DummyEmbedding())
    monkeypatch.setattr(hybrid, "async_session_factory", lambda: _DummySessionContext(rows))
    monkeypatch.setattr(hybrid, "get_reranker", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    results = await hybrid.hybrid_search("query", top_k=1)

    assert results[0]["id"] == "a"
