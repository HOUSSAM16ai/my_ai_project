# app/services/ai_service_gateway.py
"""
AI Service Gateway - Refactored for Streaming RESTful Architecture
=====================================================================
Version: 2.0.0

This module acts as a gateway between the Flask application (Overmind) and the
standalone FastAPI-based AI service. It handles the complexities of making
authenticated, streaming requests to the AI service.

Key Responsibilities:
- Generating short-lived JWTs for secure inter-service communication.
- Making streaming POST requests to the AI service.
- Relaying the streamed response chunks back to the client.
- Centralized error handling and configuration management for AI service interaction.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

import jwt
import requests
from flask import current_app

logger = logging.getLogger(__name__)

# Singleton instance of the gateway
_ai_service_gateway = None


class AIServiceGateway:
    """
    A gateway to the standalone FastAPI AI service.
    """

    def __init__(self):
        """Initializes the gateway with configuration from the Flask app."""
        self.ai_service_url = current_app.config.get("AI_SERVICE_URL")
        self.secret_key = current_app.config.get("SECRET_KEY")
        if not self.ai_service_url or not self.secret_key:
            raise ValueError("AI_SERVICE_URL and SECRET_KEY must be configured.")
        logger.info(f"AI Service Gateway initialized for URL: {self.ai_service_url}")

    def _generate_service_token(self, user_id: int | str) -> str:
        """
        Generates a short-lived JWT for authenticating with the AI service.

        Args:
            user_id: The ID of the user making the request.

        Returns:
            A JWT string.
        """
        payload = {
            "exp": datetime.now(UTC) + timedelta(minutes=5),  # Token valid for 5 mins
            "iat": datetime.now(UTC),
            "sub": str(user_id),  # Subject is the user ID
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def stream_chat(self, question: str, conversation_id: str | None, user_id: int | str):
        """
        Streams a chat response from the AI service.

        This method makes a POST request to the AI service's streaming endpoint
        and yields the data chunks as they are received.

        Args:
            question: The user's question.
            conversation_id: The ID of the ongoing conversation, if any.
            user_id: The ID of the user initiating the chat.

        Yields:
            A dictionary for each chunk of the JSON response.
        """
        if not self.ai_service_url:
            logger.error("AI Service URL is not configured.")
            yield {"type": "error", "payload": {"error": "AI service is not configured."}}
            return

        service_token = self._generate_service_token(user_id)
        headers = {
            "Authorization": f"Bearer {service_token}",
            "Content-Type": "application/json",
        }
        payload = {"question": question, "conversation_id": conversation_id}
        stream_url = f"{self.ai_service_url}/api/v1/chat/stream"

        try:
            with requests.post(
                stream_url, headers=headers, json=payload, stream=True, timeout=120
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            # Decode the line and parse the JSON chunk
                            chunk = json.loads(line.decode("utf-8"))
                            yield chunk
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON chunk: {line}")
                            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to AI service at {stream_url}: {e}", exc_info=True)
            yield {
                "type": "error",
                "payload": {"error": f"Could not connect to the AI service: {e}"},
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during AI stream: {e}", exc_info=True)
            yield {"type": "error", "payload": {"error": f"An unexpected error occurred: {e}"}}


def get_ai_service_gateway() -> AIServiceGateway:
    """
    Factory function to get the singleton instance of the AIServiceGateway.
    This ensures that we reuse the same gateway instance across the application.

    Returns:
        The singleton AIServiceGateway instance.
    """
    global _ai_service_gateway
    if _ai_service_gateway is None:
        try:
            _ai_service_gateway = AIServiceGateway()
        except ValueError as e:
            # This will happen if the app is not configured correctly.
            # We log the error but don't raise it, allowing the app to start
            # but endpoints will fail gracefully.
            logger.error(f"Failed to initialize AI Service Gateway: {e}")
            return None  # Return None to indicate failure
    return _ai_service_gateway


__all__ = ["AIServiceGateway", "get_ai_service_gateway"]
