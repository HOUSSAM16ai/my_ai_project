
from dataclasses import dataclass
from datetime import datetime

from app.core.domain_events import (
    AccessDenied,
    ApiRequestReceived,
    ApiResponseSent,
    BoundedContext,
    ChatIntentDetected,
    DataExportRequested,
    DomainEvent,
    DomainEventRegistry,
    EventCategory,
    MissionCompleted,
    MissionCreated,
    MissionCreatedFromChat,
    MissionFailed,
    MissionStarted,
    NotificationRequested,
    RateLimitExceeded,
    SecurityThreatDetected,
    TaskAssigned,
    TaskCompleted,
    TaskCreated,
    TaskFailed,
    TaskStarted,
    ToolExecutionCompleted,
    ToolExecutionStarted,
    UserCreated,
    UserDeleted,
    UserUpdated,
)


class TestDomainEvents:

    def test_base_event_initialization(self):
        event = DomainEvent(
            event_type="TestEvent",
            payload={"key": "value"}
        )
        assert event.event_id is not None
        assert isinstance(event.occurred_at, datetime)
        assert event.event_type == "TestEvent"
        assert event.payload == {"key": "value"}

    def test_event_post_init_sets_type(self):
        @dataclass
        class CustomEvent(DomainEvent):
            def __init__(self):
                super().__init__(event_type="")

        event = CustomEvent()
        assert event.event_type == "CustomEvent"

    def test_user_events(self):
        e1 = UserCreated("u1", "test@example.com", "Test User")
        assert e1.bounded_context == BoundedContext.USER_MANAGEMENT
        assert e1.aggregate_id == "u1"
        assert e1.payload["email"] == "test@example.com"

        e2 = UserUpdated("u1", {"name": "New Name"})
        assert e2.payload["changes"]["name"] == "New Name"

        e3 = UserDeleted("u1", "gdpr")
        assert e3.payload["reason"] == "gdpr"

    def test_mission_events(self):
        e1 = MissionCreated("m1", "Objective")
        assert e1.bounded_context == BoundedContext.MISSION_ORCHESTRATION
        assert e1.aggregate_type == "Mission"

        e2 = MissionStarted("m1", "user1")
        assert e2.payload["started_by"] == "user1"

        e3 = MissionCompleted("m1", "Success", 10.5)
        assert e3.payload["duration_seconds"] == 10.5

        e4 = MissionFailed("m1", "Error", "t1")
        assert e4.payload["error"] == "Error"

    def test_task_events(self):
        e1 = TaskCreated("t1", "m1", "Desc")
        assert e1.bounded_context == BoundedContext.TASK_EXECUTION

        e2 = TaskAssigned("t1", "agent1", "system")
        assert e2.payload["assigned_to"] == "agent1"

        e3 = TaskStarted("t1", "agent1")
        assert e3.payload["executor"] == "agent1"

        e4 = TaskCompleted("t1", "Result", 5.0)
        assert e4.payload["result"] == "Result"

        e5 = TaskFailed("t1", "Error", 1)
        assert e5.payload["retry_count"] == 1

    def test_security_events(self):
        e1 = SecurityThreatDetected("SQLi", "High", "1.1.1.1", {})
        assert e1.bounded_context == BoundedContext.SECURITY_COMPLIANCE
        assert e1.category == EventCategory.SYSTEM

        e2 = AccessDenied("u1", "/admin", "Role")
        assert e2.payload["resource"] == "/admin"
        assert e2.category == EventCategory.SYSTEM

    def test_api_events(self):
        e1 = ApiRequestReceived("req1", "GET", "/api")
        assert e1.bounded_context == BoundedContext.API_GATEWAY
        assert e1.category == EventCategory.SYSTEM

        e2 = ApiResponseSent("req1", 200, 100.0)
        assert e2.payload["status_code"] == 200
        assert e2.category == EventCategory.SYSTEM

        e3 = RateLimitExceeded("c1", "/api", 10)
        assert e3.payload["limit"] == 10
        assert e3.category == EventCategory.SYSTEM

    def test_chat_events(self):
        e1 = ChatIntentDetected("conv1", "u1", "help", 0.9, "I need help")
        assert e1.bounded_context == BoundedContext.ADMIN_OPERATIONS
        assert e1.payload["confidence"] == 0.9

        e2 = ToolExecutionStarted("tool1", "u1", "conv1", {})
        assert e2.bounded_context == BoundedContext.TASK_EXECUTION

        e3 = ToolExecutionCompleted("tool1", "u1", "conv1", True, 100.0)
        assert e3.payload["success"] is True

        e4 = MissionCreatedFromChat("m1", "conv1", "u1", "Obj")
        assert e4.payload["conversation_id"] == "conv1"

    def test_integration_events(self):
        e1 = NotificationRequested("email", "u1", "Subj", "Body")
        assert e1.bounded_context == BoundedContext.NOTIFICATION_DELIVERY
        assert e1.category == EventCategory.INTEGRATION

        e2 = DataExportRequested("ex1", "csv", {})
        assert e2.bounded_context == BoundedContext.ANALYTICS_REPORTING
        assert e2.category == EventCategory.INTEGRATION

    def test_registry(self):
        # All events should be auto-registered
        assert DomainEventRegistry.get_event_class("UserCreated") == UserCreated
        assert "MissionCreated" in DomainEventRegistry.list_events()

        # Test manual registration
        @dataclass
        class ManualEvent(DomainEvent):
            pass
        DomainEventRegistry.register(ManualEvent)
        assert DomainEventRegistry.get_event_class("ManualEvent") == ManualEvent
