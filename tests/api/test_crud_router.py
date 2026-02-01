"""Tests for CRUD router."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.crud import get_crud_service, router
from app.schemas.management import PaginatedResponse as BoundaryPaginatedResponse
from app.schemas.management import PaginationMeta


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_service():
    return AsyncMock()


def test_list_resources_success(client, mock_service):
    # Setup mock result
    items = [{"id": 1, "name": "Res 1"}, {"id": 2, "name": "Res 2"}]
    boundary_result = BoundaryPaginatedResponse(
        items=items,
        pagination=PaginationMeta(
            total_items=2, page=1, per_page=10, total_pages=1, has_next=False, has_prev=False
        ),
    )
    mock_service.list_items.return_value = boundary_result

    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.get("/resources/users?page=1&per_page=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 1


def test_list_resources_invalid_type(client, mock_service):
    mock_service.list_items.side_effect = ValueError("Invalid resource type")
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.get("/resources/invalid")
    assert response.status_code == 400
    assert "Invalid resource type" in response.json()["detail"]


def test_create_resource(client, mock_service):
    mock_service.create_item.return_value = {"id": 123, "name": "New"}
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.post("/resources/users", json={"name": "New"})
    assert response.status_code == 200
    assert response.json()["id"] == 123


def test_get_resource_success(client, mock_service):
    mock_service.get_item.return_value = {"id": "abc", "data": "val"}
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.get("/resources/users/abc")
    assert response.status_code == 200
    assert response.json()["id"] == "abc"


def test_get_resource_not_found(client, mock_service):
    mock_service.get_item.return_value = None
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.get("/resources/users/abc")
    assert response.status_code == 404


def test_update_resource(client, mock_service):
    mock_service.update_item.return_value = {"id": "abc", "updated": True}
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.put("/resources/users/abc", json={"updated": True})
    assert response.status_code == 200
    assert response.json()["updated"] is True


def test_delete_resource(client, mock_service):
    mock_service.delete_item.return_value = {"id": "abc", "deleted": True}
    client.app.dependency_overrides[get_crud_service] = lambda: mock_service

    response = client.delete("/resources/users/abc")
    assert response.status_code == 200
    assert response.json()["id"] == "abc"
