from fastapi.testclient import TestClient

from app.api.main import create_app

app = create_app()
client = TestClient(app)


def test_health_check():
    response = client.get("/system/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
