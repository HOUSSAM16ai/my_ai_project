# tests/test_ai_service.py
import json
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from ai_service_standalone.main import ALGORITHM, SECRET_KEY, app

client = TestClient(app)

def test_stream_chat_endpoint():
    token = jwt.encode(
        {
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
            "sub": "123",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": "Hello, world!"}

    response = client.post("/api/v1/chat/stream", headers=headers, json=payload)
    assert response.status_code == 200

    # Collect and parse the streaming response
    lines = response.text.strip().split('\n')
    chunks = [json.loads(line.replace("data: ", "")) for line in lines if line]

    assert len(chunks) > 0

    # Reconstruct the full response
    full_content = "".join(c['payload']['content'] for c in chunks if c['type'] == 'data')

    assert "Hello, world!" in full_content
    assert chunks[-1]['type'] == 'end'
