# tests/_helpers.py
import json
from typing import Any

def parse_response_json(response: Any) -> Any:
    """
    Unified JSON parsing helper for FastAPI TestClient responses.
    """
    try:
        return response.json()
    except json.JSONDecodeError:
        # Fallback for empty or non-JSON responses
        return response.text
