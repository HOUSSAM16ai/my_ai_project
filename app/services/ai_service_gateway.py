# app/services/ai_service_gateway.py
"""
AI Service Gateway - Enterprise Communication Protocol
======================================================
Version: 1.0.0
Author: Your Name
"""

import json
import os
from datetime import UTC, datetime, timedelta

import jwt
import requests
from flask import current_app


class AIServiceGateway:
    """
    A centralized gateway for all communications with the FastAPI AI service.
    """

    def __init__(self):
        self.base_url = os.environ.get("AI_SERVICE_BASE_URL", "http://localhost:8000")
        self.timeout = int(os.environ.get("AI_SERVICE_TIMEOUT", 30))
        self.secret_key = os.environ.get("SECRET_KEY", "your-super-secret-key")
        self.algorithm = "HS256"

    def _generate_token(self):
        """
        Generates a short-lived JWT to authenticate with the AI service.
        """
        payload = {
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "iat": datetime.now(UTC),
            "sub": "flask-frontend" # Service-to-service authentication
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def stream_chat(self, question: str, conversation_id: str = None):
        """
        Streams a chat response from the AI service.
        """
        url = f"{self.base_url}/api/v1/chat/stream"
        headers = {
            "Authorization": f"Bearer {self._generate_token()}",
            "Content-Type": "application/json",
            "Accept": "application/x-ndjson"
        }
        payload = {
            "question": question,
            "conversation_id": conversation_id
        }

        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield json.loads(line)
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error streaming from AI service: {e}")
            yield {
                "type": "error",
                "payload": {
                    "error_message": str(e)
                }
            }

def get_ai_service_gateway():
    """
    Factory function to get an instance of the AI Service Gateway.
    """
    return AIServiceGateway()
