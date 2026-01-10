import json
from typing import Any

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.agents.api_contract import APIContractAgent
from app.services.chat.agents.base import AgentResponse
from app.services.chat.agents.data_access import DataAccessAgent
from app.services.chat.agents.refactor import RefactorAgent
from app.services.chat.agents.test_agent import TestAgent
from app.services.chat.tools import ToolRegistry

logger = get_logger("orchestrator-agent")

class OrchestratorAgent:
    """
    The master agent that coordinates others and routes tools.
    Owns planning, state, and final merge.
    """

    def __init__(self, ai_client: AIClient, tools: ToolRegistry) -> None:
        self.ai_client = ai_client
        self.tools = tools
        self.api_agent = APIContractAgent()
        self.data_agent = DataAccessAgent()
        self.refactor_agent = RefactorAgent()
        self.test_agent = TestAgent()

    async def run(self, question: str, context: dict[str, Any] | None = None) -> str:
        """
        Main execution loop.
        1. Parse intent/plan.
        2. Consult sub-agents.
        3. Execute tools.
        4. Synthesize response.
        """
        logger.info(f"Orchestrator received: {question}")

        response_text = ""

        # Case 1: User Count
        if "how many users" in question.lower() or "count users" in question.lower():
            # Governance checks
            gov_response = await self.data_agent.process({"entity": "user", "operation": "count", "access_method": "service_api"})
            if not gov_response.success:
                return f"Governance Error: {gov_response.message}"

            # Execute Tool
            try:
                count = await self.tools.execute("get_user_count", {})
                response_text = f"There are currently {count} users in the system."
            except Exception as e:
                response_text = f"Failed to retrieve user count: {e}"

        # Case 2: Find File/Feature
        elif "find" in question.lower() or "locate" in question.lower() or "search" in question.lower():
            query = question.replace("find", "").replace("locate", "").replace("search", "").strip()
            # Governance checks
            gov_response = await self.refactor_agent.process({})
            if not gov_response.success:
                return f"Governance Error: {gov_response.message}"

            # Execute Tool
            try:
                results = await self.tools.execute("search_codebase", {"query": query})
                if results:
                    response_text = f"Found matches for '{query}':\n"
                    # Limit output
                    for loc in results[:5]:
                        response_text += f"- {loc['file_path']}"
                        if loc.get('line_number'):
                            response_text += f":{loc['line_number']}"
                        response_text += "\n"
                else:
                    response_text = f"No results found for '{query}'."
            except Exception as e:
                response_text = f"Error searching codebase: {e}"

        # Default: Fallback to simple echo or AI response (simulated here)
        else:
             response_text = "I am the Admin Assistant. I can help you count users or find code features. Please be specific."

        return response_text
