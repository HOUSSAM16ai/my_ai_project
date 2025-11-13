import pytest
from fastapi.testclient import TestClient
from ai_service_standalone.main import app, SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime, timedelta, timezone

client = TestClient(app)


def test_websocket_connection():
    token = jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "sub": "123",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text(token)
        response = websocket.receive_text()
        assert "Authentication successful" in response
