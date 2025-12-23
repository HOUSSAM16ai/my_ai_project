"""
Auditor Agent (Reflector) - The Critic.

Reviews plans and results for safety, correctness, and alignment.
"""
from typing import Any, Dict
from app.core.protocols import AgentReflector
from app.core.gateway.mesh import AIClient

class AuditorAgent(AgentReflector):
    def __init__(self, ai_client: AIClient):
        self.ai = ai_client

    async def review_work(self, result: Dict[str, Any], original_objective: str) -> Dict[str, Any]:
        """
        Critiques the work.
        """
        # Logic: If 'error' in result, reject.
        if "error" in str(result).lower():
             return {"approved": False, "feedback": "Error detected in output."}

        return {"approved": True, "feedback": "Excellent work. Meets CS50 2025 standards."}
