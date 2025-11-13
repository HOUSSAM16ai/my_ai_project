from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from ai_service_standalone.main import ALGORITHM, SECRET_KEY, app

client = TestClient(app)


def test_websocket_connection():
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
            "sub": "123",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text(token)
        response = websocket.receive_text()
        assert "Authentication successful" in response
