# app/services/chat/answering/llm_invoker.py
"""LLM invoker with CC ≤ 4."""

from typing import Any


class LLMInvoker:
    """Invokes LLM for answers. CC ≤ 4"""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def invoke(self, question: str, context: dict) -> dict[str, Any]:
        """Invoke LLM with retries. CC=4"""
        for attempt in range(self.max_retries):
            try:
                result = self._call_llm(question, context)

                if self._is_valid_response(result):
                    return result

                if attempt < self.max_retries - 1:
                    continue

                return {"error": "Empty response after retries"}

            except Exception as e:
                if attempt < self.max_retries - 1:
                    continue
                return {"error": str(e)}

        return {"error": "Max retries exceeded"}

    def _call_llm(self, question: str, context: dict) -> dict:
        """Call LLM API. CC=2"""
        # Placeholder - actual implementation would call real LLM
        return {"content": f"Answer to: {question}", "tokens": 100, "model": "test-model"}

    def _is_valid_response(self, result: dict) -> bool:
        """Check if response is valid. CC=2"""
        return "content" in result and result["content"].strip() != ""
