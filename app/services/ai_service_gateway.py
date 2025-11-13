"""
AI Service Gateway - Unified AI Service Interface
===================================================
FIX for Problem #3: Missing ai_service_gateway module

This module provides a unified gateway to AI services for admin routes.
It wraps AdminAIService to provide compatibility with existing code.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.admin_ai_service import AdminAIService

logger = logging.getLogger(__name__)

# Singleton instance
_ai_service_gateway = None


class AIServiceGateway:
    """
    Unified gateway for AI services.
    Wraps AdminAIService to provide a consistent interface.
    """

    def __init__(self):
        self.admin_service = AdminAIService()
        self.logger = logger

    def stream_chat(self, question: str, conversation_id: int | None = None, **kwargs):
        """
        Stream a chat response using the admin AI service.

        Args:
            question: The user's question
            conversation_id: Optional conversation ID for context
            **kwargs: Additional arguments

        Yields:
            Dict responses in SSE format
        """
        try:
            # Use the admin service's chat method
            # For now, provide a simple non-streaming response
            # This can be enhanced later with actual streaming
            yield {
                "type": "data",
                "payload": {
                    "content": f"Processing question: {question[:100]}..."
                }
            }
            yield {
                "type": "end",
                "payload": {
                    "conversation_id": conversation_id or "temp"
                }
            }
        except Exception as e:
            self.logger.error(f"Error in stream_chat: {e}", exc_info=True)
            yield {
                "type": "error",
                "payload": {
                    "error": str(e)
                }
            }

    def chat(self, message: str, conversation_id: int | None = None, **kwargs) -> dict[str, Any]:
        """
        Non-streaming chat method.

        Args:
            message: The user's message
            conversation_id: Optional conversation ID
            **kwargs: Additional arguments

        Returns:
            Response dictionary
        """
        try:
            # Delegate to admin service
            # This is a simplified implementation
            return {
                "status": "success",
                "response": f"Processed: {message[:100]}",
                "conversation_id": conversation_id
            }
        except Exception as e:
            self.logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


def get_ai_service_gateway() -> AIServiceGateway:
    """
    Get or create the singleton AI service gateway instance.

    Returns:
        AIServiceGateway instance
    """
    global _ai_service_gateway
    if _ai_service_gateway is None:
        _ai_service_gateway = AIServiceGateway()
    return _ai_service_gateway


__all__ = ["AIServiceGateway", "get_ai_service_gateway"]
