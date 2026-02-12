from typing import Any

from app.core.logging import get_logger
from app.core.settings.base import get_settings
from app.integration.protocols.research_gateway import ResearchGatewayProtocol

logger = get_logger(__name__)

class LocalResearchGateway(ResearchGatewayProtocol):
    """
    Local Adapter for the Research Agent.
    Implements the ResearchGatewayProtocol by directly importing the microservice code.
    This acts as an Anti-Corruption Layer (ACL) preventing direct coupling in the core app.
    """

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Executes semantic search using the local Research Agent module.
        """
        try:
            from microservices.research_agent.src.search_engine import get_retriever

            # Use real database settings
            db_url = str(get_settings().database.url)
            retriever = get_retriever(db_url)
            return await retriever.search(query, top_k=top_k, filters=filters)

        except ImportError as e:
            logger.error(f"Research Agent module not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in semantic_search: {e}")
            raise

    async def refine_query(
        self,
        query: str,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Refines a query using DSPy from the local Research Agent module.
        """
        try:
            from microservices.research_agent.src.search_engine.query_refiner import (
                get_refined_query,
            )
            return get_refined_query(query, api_key)
        except ImportError as e:
            logger.error(f"Research Agent module not found: {e}")
            raise
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
        Reranks results using the local Research Agent module.
        """
        try:
            from microservices.research_agent.src.search_engine.reranker import (
                get_reranker,
            )
            reranker = get_reranker()
            return reranker.rerank(query, documents, top_n=top_n)
        except ImportError as e:
            logger.error(f"Research Agent module not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in rerank_results: {e}")
            raise

    def get_llamaindex_status(self) -> dict[str, Any]:
        try:
            from microservices.research_agent.src.search_engine import (  # noqa: F401
                LlamaIndexRetriever,
            )
            return {
                "status": "active",
                "capabilities": ["semantic_search", "metadata_filtering", "reranking"],
            }
        except ImportError:
            return {"status": "unavailable"}

    def get_dspy_status(self) -> dict[str, Any]:
        try:
            import dspy  # noqa: F401
            return {
                "status": "active",
                "modules": ["GeneratePlan", "CritiquePlan", "QueryRefiner"],
            }
        except ImportError:
            return {"status": "unavailable"}

    def get_reranker_status(self) -> dict[str, Any]:
        try:
            from microservices.research_agent.src.search_engine.reranker import (  # noqa: F401
                Reranker,
            )
            return {
                "status": "active",
                "model": "BAAI/bge-reranker-base",
            }
        except ImportError:
            return {"status": "unavailable"}
