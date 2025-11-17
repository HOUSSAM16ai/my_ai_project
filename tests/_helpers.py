import json
from typing import Any

def parse_response_json(response: Any) -> Any:
    """
    Unified JSON parsing helper to normalize TestClient responses across Flask, FastAPI, and Starlette.

    Priority:
    1) response.json()  (FastAPI/Starlette/TestClient)
    2) response.get_json()  (Flask)
    3) json.loads(response.data / response.content / response.body)
    """
    try:
        # FastAPI / Starlette
        if hasattr(response, "json") and callable(response.json):
            return response.json()

        # Flask
        if hasattr(response, "get_json") and callable(response.get_json):
            return response.get_json()

        # Raw content
        data = (
            getattr(response, "data", None)
            or getattr(response, "content", None)
            or getattr(response, "body", None)
        )

        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")

        return json.loads(data) if data else None
    except Exception:
        raise  # Visible stacktrace for debugging
