"""
اختبارات واجهات تخطيط الوكلاء.
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.services.overmind.domain.api_schemas import AgentPlanData, AgentPlanStepResponse
from app.services.overmind.plan_registry import AgentPlanRecord


class StubPlanService:
    """خدمة تخطيط بديلة لتجنب الاعتماد على الذكاء الاصطناعي أثناء الاختبار."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def create_plan(self, payload) -> AgentPlanRecord:
        step = AgentPlanStepResponse(
            step_id="step-01",
            title="تحليل الهدف",
            description="جمع المعطيات وتحليل المشكلة.",
            dependencies=[],
            estimated_effort="1 ساعة",
        )
        plan_data = AgentPlanData(
            plan_id="plan_test_001",
            objective=payload.objective,
            steps=[step],
            created_at=datetime.now(UTC),
        )
        return AgentPlanRecord(data=plan_data)


def test_agents_plan_create_and_fetch(
    client: TestClient,
    admin_auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    """يتحقق من إنشاء الخطة واسترجاعها عبر الـ API."""
    monkeypatch.setattr(client.app.state, "agent_plan_service", StubPlanService())

    response = client.post(
        "/api/v1/agents/plan",
        json={
            "objective": "تصميم واجهة API",
            "context": {"scope": "contract-first"},
            "constraints": ["OpenAPI v3.1"],
            "priority": "high",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["plan_id"] == "plan_test_001"

    plan_id = payload["data"]["plan_id"]
    fetch_response = client.get(f"/api/v1/agents/plan/{plan_id}", headers=admin_auth_headers)
    assert fetch_response.status_code == 200
    fetch_payload = fetch_response.json()
    assert fetch_payload["data"]["plan_id"] == plan_id


def test_agents_plan_missing_returns_404(
    client: TestClient,
    admin_auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    """يتحقق من إرجاع 404 عند طلب خطة غير موجودة."""
    monkeypatch.setattr(client.app.state, "agent_plan_service", StubPlanService())

    response = client.get("/api/v1/agents/plan/plan_missing", headers=admin_auth_headers)
    assert response.status_code == 404


def test_agents_plan_requires_auth(client: TestClient, monkeypatch) -> None:
    """يتحقق من رفض الطلبات دون ترويسات المصادقة."""
    monkeypatch.setattr(client.app.state, "agent_plan_service", StubPlanService())

    response = client.post(
        "/api/v1/agents/plan",
        json={
            "objective": "خطة بدون مصادقة",
            "context": {},
            "constraints": [],
            "priority": "low",
        },
    )
    assert response.status_code == 401
