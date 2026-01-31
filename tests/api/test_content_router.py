"""Tests for Content router."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.content import router
from app.core.database import get_db


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock()


def test_search_content_empty(client, mock_db):
    # Mock execute to return empty result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    client.app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/v1/content/search")

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_search_content_with_results(client, mock_db):
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("id1", "exercise", "Title 1", "L1", "math", 2024, "en"),
        ("id2", "lesson", "Title 2", "L2", "physics", 2023, "fr"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)

    client.app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/v1/content/search?level=L1")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["id"] == "id1"


def test_get_content_not_found(client, mock_db):
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    client.app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/v1/content/nonexistent-id")

    assert response.status_code == 404


def test_get_content_raw_not_found(client, mock_db):
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    client.app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/v1/content/nonexistent-id/raw")

    assert response.status_code == 404


def test_get_solution_not_found(client, mock_db):
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    client.app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/v1/content/nonexistent-id/solution")

    assert response.status_code == 404
