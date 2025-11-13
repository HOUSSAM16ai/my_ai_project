# app/services/ai_service_gateway.py
import requests
import json
from flask import current_app

class AIServiceGateway:
    def __init__(self, base_url):
        self.base_url = base_url

    def stream_chat(self, question, conversation_id=None):
        """Streams chat responses from the AI service."""
        payload = {
            "question": question,
            "conversation_id": conversation_id
        }
        url = f"{self.base_url}/api/v1/chat/stream"

        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line.startswith(b'data: '):
                        try:
                            data_str = line.decode('utf-8')[6:]
                            if data_str.strip():
                                yield json.loads(data_str)
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            current_app.logger.error(f"Error decoding stream data: {e}")
                            continue
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"AI service request failed: {e}")
            yield {"type": "error", "payload": {"error_message": "Failed to connect to AI service."}}

def get_ai_service_gateway():
    """Factory function for the AI Service Gateway."""
    # This could be configured via Flask config
    ai_service_url = current_app.config.get("AI_SERVICE_URL", "http://127.0.0.1:8001")
    return AIServiceGateway(base_url=ai_service_url)
