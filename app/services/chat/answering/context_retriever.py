# app/services/chat/answering/context_retriever.py
"""Context retriever with CC ≤ 3."""

from typing import Any


class ContextRetriever:
    """Retrieves context for questions. CC ≤ 3"""
    
    def retrieve(self, question: str, context: dict) -> dict[str, Any]:
        """Retrieve relevant context. CC=3"""
        result = {
            "question": question,
            "history": context.get("history", []),
            "user_info": context.get("user", {}),
        }
        
        if context.get("use_deep_context"):
            result["deep_context"] = self._get_deep_context(question)
        
        return result
    
    def _get_deep_context(self, question: str) -> dict:
        """Get deep context. CC=2"""
        # Placeholder for deep context retrieval
        return {"source": "deep", "relevance": 0.8}
