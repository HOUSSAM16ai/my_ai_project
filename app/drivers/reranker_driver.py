from typing import Any

from app.core.integration_kernel.contracts import RankingEngine
from app.core.integration_kernel.ir import ScoringSpec
from app.core.logging import get_logger

logger = get_logger(__name__)

class RerankerDriver(RankingEngine):
    """
    Driver for Reranker operations.
    Currently delegates to the LocalResearchGateway.
    """
    async def rank(self, spec: ScoringSpec) -> dict[str, Any]:
        """
        Ranks a list of documents against a query using a CrossEncoder or similar.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway
            gateway = LocalResearchGateway()

            reranked = await gateway.rerank_results(spec.query, spec.documents, top_n=spec.top_n)

            return {
                "success": True,
                "query": spec.query,
                "reranked_results": reranked,
            }
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """
        Returns the health status of the ranking engine.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway
            return LocalResearchGateway().get_reranker_status()
        except ImportError:
            return {"status": "unavailable", "error": "ResearchGateway missing"}
