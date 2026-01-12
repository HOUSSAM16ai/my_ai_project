from __future__ import annotations

from datetime import datetime

from app.schemas.management import (
    GenericResponse,
    MissionResponse,
    PaginatedResponse,
    PaginationMeta,
    TaskResponse,
    UserResponse,
)


def test_generic_response_keeps_payload_type():
    response = GenericResponse[int](data=7)

    assert response.status == "success"
    assert response.data == 7


def test_paginated_response_shapes_payload_consistently():
    pagination = PaginationMeta(
        page=1, per_page=5, total_items=12, total_pages=3, has_next=True, has_prev=False
    )
    tasks = [TaskResponse(id=idx, name=f"Task {idx}") for idx in range(2)]

    payload = PaginatedResponse[TaskResponse](items=tasks, pagination=pagination)

    assert payload.items == tasks
    assert payload.pagination.total_pages == 3


def test_user_and_mission_responses_allow_optional_fields():
    user = UserResponse(id=1, email="admin@example.test", created_at=datetime(2024, 1, 1))
    mission = MissionResponse(id=5, name=None, objective=None, status=None)

    assert user.email == "admin@example.test"
    assert user.created_at.year == 2024
    assert mission.name is None
    assert mission.status is None
