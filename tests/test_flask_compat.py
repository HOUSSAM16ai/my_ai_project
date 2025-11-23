import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.kernel_v2.compat_collapse import g, request, current_user, jsonify
from app.middleware.adapters.flask_compat import FlaskCompatMiddleware

app = FastAPI()
app.add_middleware(FlaskCompatMiddleware)


@app.get("/test-g")
async def endpoint_g():
    g.foo = "bar"
    return {"foo": g.foo}


@app.get("/test-request")
async def endpoint_request():
    return {"method": request.method, "url": str(request.url)}


@app.get("/test-user")
async def endpoint_user():
    return {"is_authenticated": current_user.is_authenticated}


@app.get("/test-jsonify")
async def endpoint_jsonify():
    return jsonify({"message": "hello"})


client = TestClient(app)


def test_g_context():
    response = client.get("/test-g")
    assert response.status_code == 200
    assert response.json() == {"foo": "bar"}


def test_request_proxy():
    response = client.get("/test-request")
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "GET"
    assert "/test-request" in data["url"]


def test_current_user_default():
    response = client.get("/test-user")
    assert response.status_code == 200
    assert response.json() == {"is_authenticated": False}


def test_jsonify_helper():
    response = client.get("/test-jsonify")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_g_outside_context():
    with pytest.raises(RuntimeError, match="Working outside of application context"):
        g.foo = "bar"


def test_request_outside_context():
    with pytest.raises(RuntimeError, match="Working outside of request context"):
        _ = request.method
