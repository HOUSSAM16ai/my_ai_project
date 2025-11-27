
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_chat_stream_value_error_400():
    response = client.post("/admin/api/chat/stream", json={"question": "This will raise a ValueError"})
    assert response.status_code == 400
    assert response.json() == {"message": "An error occurred", "error": "OPENROUTER_API_key is not set."}
