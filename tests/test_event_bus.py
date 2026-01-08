"""
اختبارات ناقل الأحداث (Event Bus Tests).

يختبر هذا الملف جميع وظائف ناقل الأحداث بما في ذلك:
- النشر والاشتراك
- معالجة الأحداث
- السجل
- معالجة الأخطاء
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.core.event_bus_impl import Event, EventBus, get_event_bus


class TestEvent:
    """اختبارات نموذج الحدث."""
    
    def test_event_creation(self) -> None:
        """يختبر إنشاء حدث."""
        event = Event(
            event_id=uuid4(),
            event_type="test.event",
            payload={"key": "value"},
            timestamp=datetime.utcnow(),
            source="test-service",
        )
        
        assert event.event_type == "test.event"
        assert event.payload == {"key": "value"}
        assert event.source == "test-service"
    
    def test_event_immutability(self) -> None:
        """يختبر ثبات الحدث."""
        event = Event(
            event_id=uuid4(),
            event_type="test.event",
            payload={},
            timestamp=datetime.utcnow(),
            source="test",
        )
        
        with pytest.raises(AttributeError):
            event.event_type = "modified"  # type: ignore


class TestEventBus:
    """اختبارات ناقل الأحداث."""
    
    def test_bus_initialization(self) -> None:
        """يختبر تهيئة الناقل."""
        bus = EventBus()
        
        assert bus is not None
        assert len(bus.get_all_event_types()) == 0
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self) -> None:
        """يختبر الاشتراك والنشر."""
        bus = EventBus()
        received_events = []
        
        @bus.subscribe("test.event")
        async def handler(event: Event) -> None:
            received_events.append(event)
        
        await bus.publish(
            event_type="test.event",
            payload={"message": "hello"},
            source="test",
        )
        
        assert len(received_events) == 1
        assert received_events[0].event_type == "test.event"
        assert received_events[0].payload["message"] == "hello"
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self) -> None:
        """يختبر عدة مشتركين لنفس الحدث."""
        bus = EventBus()
        handler1_called = []
        handler2_called = []
        
        @bus.subscribe("test.event")
        async def handler1(event: Event) -> None:
            handler1_called.append(True)
        
        @bus.subscribe("test.event")
        async def handler2(event: Event) -> None:
            handler2_called.append(True)
        
        await bus.publish(
            event_type="test.event",
            payload={},
            source="test",
        )
        
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """يختبر إلغاء الاشتراك."""
        bus = EventBus()
        received_events = []
        
        async def handler(event: Event) -> None:
            received_events.append(event)
        
        bus.subscribe("test.event", handler)
        
        await bus.publish(
            event_type="test.event",
            payload={},
            source="test",
        )
        
        assert len(received_events) == 1
        
        bus.unsubscribe("test.event", handler)
        
        await bus.publish(
            event_type="test.event",
            payload={},
            source="test",
        )
        
        # لا يجب أن يزيد العدد
        assert len(received_events) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        """يختبر معالجة الأخطاء في المعالجات."""
        bus = EventBus()
        successful_handler_called = []
        
        @bus.subscribe("test.event")
        async def failing_handler(event: Event) -> None:
            raise ValueError("Handler error")
        
        @bus.subscribe("test.event")
        async def successful_handler(event: Event) -> None:
            successful_handler_called.append(True)
        
        # يجب أن ينشر الحدث دون رفع استثناء
        await bus.publish(
            event_type="test.event",
            payload={},
            source="test",
        )
        
        # المعالج الناجح يجب أن يُستدعى رغم فشل الآخر
        assert len(successful_handler_called) == 1
    
    @pytest.mark.asyncio
    async def test_event_history(self) -> None:
        """يختبر سجل الأحداث."""
        bus = EventBus()
        
        await bus.publish(
            event_type="test.event1",
            payload={"id": 1},
            source="test",
        )
        
        await bus.publish(
            event_type="test.event2",
            payload={"id": 2},
            source="test",
        )
        
        history = bus.get_history()
        assert len(history) == 2
        
        # تصفية حسب النوع
        filtered = bus.get_history(event_type="test.event1")
        assert len(filtered) == 1
        assert filtered[0].payload["id"] == 1
    
    def test_get_subscribers(self) -> None:
        """يختبر الحصول على المشتركين."""
        bus = EventBus()
        
        @bus.subscribe("test.event")
        async def handler1(event: Event) -> None:
            pass
        
        @bus.subscribe("test.event")
        async def handler2(event: Event) -> None:
            pass
        
        subscribers = bus.get_subscribers("test.event")
        assert len(subscribers) == 2
        assert "handler1" in subscribers
        assert "handler2" in subscribers
    
    def test_get_all_event_types(self) -> None:
        """يختبر الحصول على جميع أنواع الأحداث."""
        bus = EventBus()
        
        @bus.subscribe("event.type1")
        async def handler1(event: Event) -> None:
            pass
        
        @bus.subscribe("event.type2")
        async def handler2(event: Event) -> None:
            pass
        
        event_types = bus.get_all_event_types()
        assert len(event_types) == 2
        assert "event.type1" in event_types
        assert "event.type2" in event_types
    
    def test_clear_history(self) -> None:
        """يختبر مسح السجل."""
        bus = EventBus()
        
        # إضافة حدث يدوياً
        from uuid import uuid4
        event = Event(
            event_id=uuid4(),
            event_type="test",
            payload={},
            timestamp=datetime.utcnow(),
            source="test",
        )
        bus._event_history.append(event)
        
        assert len(bus.get_history()) == 1
        
        bus.clear_history()
        assert len(bus.get_history()) == 0


class TestGlobalEventBus:
    """اختبارات المثيل العام لناقل الأحداث."""
    
    def test_get_event_bus_singleton(self) -> None:
        """يختبر أن get_event_bus يعيد نفس المثيل."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
