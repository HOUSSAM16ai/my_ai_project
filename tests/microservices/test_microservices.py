"""
اختبارات مواصفات الخدمات المصغرة.

تتحقق من أن كل خدمة مستقلة تقدم واجهاتها الأساسية
وفق مبدأ "خدمة واحدة، وظيفة واحدة".
"""

from fastapi.testclient import TestClient

from microservices.memory_agent.main import create_app as create_memory_app
from microservices.orchestrator_service.main import create_app as create_orchestrator_app
from microservices.planning_agent.main import create_app as create_planning_app
from microservices.user_service.main import create_app as create_user_app


def test_orchestrator_lists_agents() -> None:
    """يتأكد من أن خدمة التنسيق تعيد سجل الوكلاء المعلن."""

    client = TestClient(create_orchestrator_app())
    response = client.get("/orchestrator/agents")

    assert response.status_code == 200
    payload = response.json()

    assert "agents" in payload
    assert {agent["name"] for agent in payload["agents"]} == {
        "planning-agent",
        "memory-agent",
        "user-service",
    }


def test_planning_agent_generates_plan_with_context() -> None:
    """يتحقق من أن وكيل التخطيط يولد خطوات تشمل السياق عند توفره."""

    client = TestClient(create_planning_app())
    response = client.post(
        "/plans",
        json={
            "goal": "بناء خطة تعلم الذكاء الاصطناعي",
            "context": ["مستوى مبتدئ", "مدة 4 أسابيع"],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["goal"] == "بناء خطة تعلم الذكاء الاصطناعي"
    assert any("تضمين السياق" in step for step in payload["steps"])


def test_memory_agent_stores_and_searches_entries() -> None:
    """يضمن أن وكيل الذاكرة يحفظ العناصر ويعيدها عبر البحث."""

    client = TestClient(create_memory_app())
    create_response = client.post(
        "/memories",
        json={"content": "معلومة مهمة عن الحوسبة", "tags": ["حاسوب", "نواة"]},
    )

    assert create_response.status_code == 200
    entry_id = create_response.json()["entry_id"]

    search_response = client.get("/memories/search", params={"query": "نواة"})
    assert search_response.status_code == 200
    results = search_response.json()

    assert any(entry["entry_id"] == entry_id for entry in results)


def test_user_service_creates_and_lists_users() -> None:
    """يتأكد من أن خدمة المستخدمين تنشئ المستخدمين وتعرضهم."""

    client = TestClient(create_user_app())
    create_response = client.post(
        "/users",
        json={"name": "Amina", "email": "amina@example.com"},
    )

    assert create_response.status_code == 200

    list_response = client.get("/users")
    assert list_response.status_code == 200
    payload = list_response.json()

    assert any(user["email"] == "amina@example.com" for user in payload)


def test_user_service_rejects_invalid_email() -> None:
    """يتأكد من أن خدمة المستخدمين ترفض البريد الإلكتروني غير الصالح."""

    client = TestClient(create_user_app())
    response = client.post(
        "/users",
        json={"name": "Noura", "email": "invalid-email"},
    )

    assert response.status_code == 422
