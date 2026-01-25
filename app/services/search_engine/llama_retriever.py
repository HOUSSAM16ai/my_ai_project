from typing import List, Optional
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode

from app.services.search_engine.hybrid import hybrid_search

class KnowledgeGraphRetriever(BaseRetriever):
    """
    Retriever that uses the custom Hybrid Search (Vector + Sparse + Rerank)
    implementation to fetch nodes from Supabase.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        super().__init__()

    def _retrieve(self, query_bundle) -> List[NodeWithScore]:
        """
        Retrieve nodes given a query.
        """
        # query_bundle can be a string or QueryBundle object
        if hasattr(query_bundle, "query_str"):
            query_str = query_bundle.query_str
        else:
            query_str = str(query_bundle)

        # Call the async hybrid_search synchronously?
        # LlamaIndex retrievers are often synchronous in the _retrieve method,
        # but if we are running in an async context (FastAPI/LangGraph), we should likely use aretrieve.
        # However, BaseRetriever defines `retrieve` (sync) and `aretrieve` (async).
        # We should implement `_aretrieve` if possible, or use a runner.

        # Since our hybrid_search is async, we should strictly implement _aretrieve if using async LlamaIndex.
        # But BaseRetriever's `retrieve` might call `_retrieve`.

        # Let's implement `_aretrieve` as the primary logic and wrap `_retrieve` to run loop if needed.
        # Actually, for simplicity in our async stack, we rely on `aretrieve`.
        raise NotImplementedError("Use aretrieve for this async-native retriever.")

    async def _aretrieve(self, query_bundle) -> List[NodeWithScore]:
        if hasattr(query_bundle, "query_str"):
            query_str = query_bundle.query_str
        else:
            query_str = str(query_bundle)

        results = await hybrid_search(query_str, top_k=self.top_k)

        nodes = []
        for res in results:
            # Create TextNode
            node = TextNode(
                text=f"{res['name']}: {res['content']}",
                id_=str(res['id']),
                metadata={
                    "name": res["name"],
                    "label": res["label"],
                    "hybrid_score": res.get("hybrid_score"),
                    "rerank_score": res.get("rerank_score")
                }
            )

            # Use rerank score if available, else hybrid
            score = res.get("rerank_score", res.get("hybrid_score", 0.0))

            nodes.append(NodeWithScore(node=node, score=score))

        return nodes
