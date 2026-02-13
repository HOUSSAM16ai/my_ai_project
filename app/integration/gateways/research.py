from typing import Any

from app.core.logging import get_logger
from app.infrastructure.clients.research_client import research_client
from app.integration.protocols.research_gateway import ResearchGatewayProtocol

logger = get_logger(__name__)


class RemoteResearchGateway(ResearchGatewayProtocol):
    """
    Remote Adapter for the Research Agent.
    Implements the ResearchGatewayProtocol by using the ResearchClient (HTTP).
    This acts as an Anti-Corruption Layer (ACL) preventing direct coupling in the core app.
    """

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Executes semantic search via the Research Agent microservice.
        """
        try:
            return await research_client.semantic_search(query, top_k=top_k, filters=filters)
        except Exception as e:
            logger.error(f"Error in semantic_search: {e}")
            raise

    async def refine_query(
        self,
        query: str,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Refines a query using the Research Agent microservice.
        """
        try:
            return await research_client.refine_query(query, api_key=api_key)
        except Exception as e:
            logger.error(f"Error in refine_query: {e}")
            raise

    async def rerank_results(
        self,
        query: str,
        documents: list[str] | list[Any],
        top_n: int = 5,
    ) -> list[Any]:
        """
        Reranks results using the Research Agent microservice.
        """
        try:
            return await research_client.rerank_results(query, documents, top_n=top_n)
        except Exception as e:
            logger.error(f"Error in rerank_results: {e}")
            raise

    def get_llamaindex_status(self) -> dict[str, Any]:
        return {"status": "active", "mode": "remote-microservice"}

    def get_dspy_status(self) -> dict[str, Any]:
        return {"status": "active", "mode": "remote-microservice"}

    def get_reranker_status(self) -> dict[str, Any]:
        return {"status": "active", "mode": "remote-microservice"}


# Alias for backward compatibility
LocalResearchGateway = RemoteResearchGateway
