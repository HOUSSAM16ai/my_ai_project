from typing import Any

from app.core.integration_kernel.contracts import PromptEngine
from app.core.integration_kernel.ir import PromptProgram
from app.core.logging import get_logger

logger = get_logger(__name__)

class DSPyDriver(PromptEngine):
    """
    Driver for DSPy prompt optimization.
    Currently delegates to the LocalResearchGateway.
    """
    async def optimize(self, program: PromptProgram) -> dict[str, Any]:
        """
        Runs a DSPy program or prompt optimization.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway
            gateway = LocalResearchGateway()

            # The current integration specifically uses 'refine_query'
            # We map 'input_text' to the query.
            result = await gateway.refine_query(program.input_text, program.api_key)

            return {
                "success": True,
                "original_query": program.input_text,
                "refined_query": result.get("refined_query", program.input_text),
                "extracted_filters": {
                    "year": result.get("year"),
                    "subject": result.get("subject"),
                    "branch": result.get("branch"),
                },
            }
        except Exception as e:
            logger.error(f"DSPy optimization error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """
        Returns the health status of the DSPy engine.
        """
        try:
            from app.integration.gateways.research import LocalResearchGateway
            return LocalResearchGateway().get_dspy_status()
        except ImportError:
            return {"status": "unavailable", "error": "ResearchGateway missing"}
