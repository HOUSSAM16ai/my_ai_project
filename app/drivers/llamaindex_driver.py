from typing import Any

from app.core.integration_kernel.contracts import RetrievalEngine
from app.core.integration_kernel.ir import RetrievalQuery
from app.core.logging import get_logger

logger = get_logger(__name__)


class LlamaIndexDriver(RetrievalEngine):
    """
    Driver for LlamaIndex retrieval.
    Currently delegates to the LocalResearchGateway.
    """

    def __init__(self):
        # We initialize the gateway lazily or during registration to avoid circular imports
        pass

    async def search(self, query: RetrievalQuery) -> dict[str, Any]:
        """
        Executes a semantic search using LlamaIndex.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway

            gateway = LocalResearchGateway()

            results = await gateway.semantic_search(
                query.query, top_k=query.top_k, filters=query.filters
            )

            return {
                "success": True,
                "query": query.query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            logger.error(f"LlamaIndex search error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """
        Returns the health status of the LlamaIndex engine.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway

            return LocalResearchGateway().get_llamaindex_status()
        except ImportError:
            return {"status": "unavailable", "error": "ResearchGateway missing"}
