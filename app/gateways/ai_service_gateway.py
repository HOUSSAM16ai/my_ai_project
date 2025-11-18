# app/gateways/ai_service_gateway.py
"""
AI Service Gateway - Refactored for DI and Testability
=====================================================================
Version: 3.0.0

This module acts as a gateway between the application and the standalone
FastAPI-based AI service. It is designed with dependency injection to be
framework-agnostic and highly testable.

Key Responsibilities:
- Generating short-lived JWTs for secure inter-service communication.
- Making streaming POST requests to the AI service via an abstracted HTTP client.
- Relaying the streamed response chunks back to the client.
- Centralized error handling and configuration management.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from logging import Logger
from typing import TYPE_CHECKING

import jwt

from app.config.settings import AppSettings as Settings
from app.core.di import get_logger, get_settings
from app.protocols.http_client import HttpClient, RequestsAdapter

if TYPE_CHECKING:
    pass


class AIServiceGateway:
    """A gateway to the standalone FastAPI AI service."""

    def __init__(self, http_client: HttpClient, settings: Settings, logger: Logger):
        self.http_client = http_client
        self.settings = settings
        self.logger = logger
        self.ai_service_url = self.settings.AI_SERVICE_URL
        self.secret_key = self.settings.SECRET_KEY

        if not self.ai_service_url or not self.secret_key:
            raise ValueError("AI_SERVICE_URL and SECRET_KEY must be configured.")
        self.logger.info(f"AI Service Gateway initialized for URL: {self.ai_service_url}")

    def _generate_service_token(self, user_id: int | str) -> str:
        """Generates a short-lived JWT for authenticating with the AI service."""
        payload = {
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "iat": datetime.now(UTC),
            "sub": str(user_id),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def stream_chat(
        self, question: str, conversation_id: str | None, user_id: int | str
    ) -> Iterator[dict]:
        """Streams a chat response from the AI service."""
        if not self.ai_service_url:
            self.logger.error("AI Service URL is not configured.")
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
            with self.http_client.post(
                stream_url, headers=headers, json=payload, stream=True, timeout=120
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            yield chunk
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to decode JSON chunk: {line}")
                            continue
        except Exception as e:
            self.logger.error(
                f"Failed to connect to AI service at {stream_url}: {e}", exc_info=True
            )
            yield {
                "type": "error",
                "payload": {"error": f"Could not connect to the AI service: {e}"},
            }


# ======================================================================================
# ==                            DEPENDENCY INJECTION FACTORY                          ==
# ======================================================================================

_ai_service_gateway_singleton = None


def get_ai_service_gateway() -> AIServiceGateway:
    """Factory function to get the singleton instance of the AIServiceGateway."""
    global _ai_service_gateway_singleton
    if _ai_service_gateway_singleton is None:
        _ai_service_gateway_singleton = AIServiceGateway(
            http_client=RequestsAdapter(),
            settings=get_settings(),
            logger=get_logger(),
        )
    return _ai_service_gateway_singleton
