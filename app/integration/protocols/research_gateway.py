from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResearchGatewayProtocol(Protocol):
    """
    Protocol for Research Agent capabilities (Search, Refine, Rerank).
    Acts as an ACL to the Research Domain.
    """

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Perform semantic search.
        Returns a list of result nodes/documents.
        """
        ...

    async def refine_query(
        self,
        query: str,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Refine a user query using DSPy/LLM.
        Returns a dictionary with refined query and filters.
        """
        ...

    async def rerank_results(
        self,
        query: str,
        documents: list[str] | list[Any],
        top_n: int = 5,
    ) -> list[Any]:
        """
        Rerank a list of documents based on the query.
        Returns the reranked list.
        """
        ...

    def get_llamaindex_status(self) -> dict[str, Any]:
        """Check LlamaIndex availability."""
        ...

    def get_dspy_status(self) -> dict[str, Any]:
        """Check DSPy availability."""
        ...

    def get_reranker_status(self) -> dict[str, Any]:
        """Check Reranker availability."""
        ...
