import pytest

from app.services.overmind.langgraph.context_enricher import ContextEnricher


class DummyPayload:
    def __init__(self, text: str, metadata: dict[str, object]) -> None:
        self.text = text
        self.metadata = metadata


class DummyNode:
    def __init__(self, payload: DummyPayload) -> None:
        self.node = payload
        self.score = 0.0


class DummyRetriever:
    def __init__(self, nodes: list[DummyNode]) -> None:
        self._nodes = nodes

    def search(self, query: str, limit: int, filters: dict[str, object]) -> list[DummyNode]:
        return self._nodes[:limit]


class DummyReranker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def rerank(self, query: str, nodes: list[DummyNode], top_n: int) -> list[DummyNode]:
        self.calls.append((query, top_n))
        return list(reversed(nodes))[:top_n]


@pytest.mark.asyncio
async def test_enrich_applies_reranker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    node_a = DummyNode(DummyPayload("النص الأول", {"content_id": "a"}))
    node_b = DummyNode(DummyPayload("النص الثاني", {"content_id": "b"}))
    retriever = DummyRetriever([node_a, node_b])
    reranker = DummyReranker()

    monkeypatch.setattr(
        "app.services.overmind.langgraph.context_enricher.get_retriever",
        lambda _: retriever,
    )
    monkeypatch.setattr(
        "app.services.overmind.langgraph.context_enricher.get_reranker",
        lambda: reranker,
    )

    enricher = ContextEnricher(max_snippets=2)
    result = await enricher.enrich("اختبار التكامل", {})

    assert result.snippets[0]["text"] == "النص الثاني"
    assert result.snippets[1]["text"] == "النص الأول"
    assert reranker.calls == [("اختبار التكامل", 2)]
