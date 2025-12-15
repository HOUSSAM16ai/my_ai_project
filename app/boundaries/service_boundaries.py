"""
======================================================================================
 SERVICE BOUNDARIES - فصل الاهتمامات عبر حدود الخدمات
======================================================================================

PURPOSE (الغرض):
  تطبيق مبادئ فصل الخدمات مع التماسك العالي والاقتران المنخفض

PATTERNS IMPLEMENTED (الأنماط المطبقة):
  1. Domain-Driven Design (التصميم القائم على المجالات)
  2. Event-Driven Architecture (المعمارية الموجهة بالأحداث)
  3. API Gateway Pattern (نمط بوابة API)
  4. Circuit Breaker (قاطع الدائرة)
  5. Bulkhead Pattern (نمط الحاجز)
  6. Timeout & Fallback (المهلة والاستجابة البديلة)

KEY PRINCIPLES (المبادئ الأساسية):
  - كل خدمة مستقلة تماماً في دورة حياتها
  - كل خدمة قابلة للفهم دون الحاجة لفهم الخدمات الأخرى
  - كل خدمة قابلة للاستبدال دون التأثير على النظام الكلي
  - فصل زمني عبر الأحداث (الناشر لا يعرف المستهلكين)
  - عزل الفشل (فشل خدمة لا يسبب انهيار النظام)

IMPLEMENTATION DATE: 2025-11-05
VERSION: 1.0.0
======================================================================================
"""
from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
logger = logging.getLogger(__name__)


class BoundedContext(ABC):
    """
    المجال الفرعي المحدود (Bounded Context)

    كل خدمة تعمل ضمن سياق محدد مع:
    - لغة محددة خاصة بالمجال (Ubiquitous Language)
    - نماذج بيانات مستقلة (Domain Models)
    - قواعد عمل خاصة (Business Rules)
    - واجهات محددة بوضوح (Well-defined Interfaces)
    """

    def __init__(self, context_name: str):
        self.context_name = context_name
        self.domain_models: dict[str, type] = {}
        self.business_rules: list[Callable] = []
        self.interfaces: dict[str, Callable] = {}

    @abstractmethod
    def get_ubiquitous_language(self) ->dict[str, str]:
        """الحصول على اللغة المحددة خاصة بالمجال"""
        pass

    @abstractmethod
    def validate_business_rules(self, data: dict[str, Any]) ->bool:
        """التحقق من قواعد العمل الخاصة بهذا المجال"""
        pass


class EventType(Enum):
    """أنواع الأحداث في النظام"""
    MISSION_CREATED = 'mission.created'
    MISSION_UPDATED = 'mission.updated'
    MISSION_COMPLETED = 'mission.completed'
    MISSION_FAILED = 'mission.failed'
    TASK_CREATED = 'task.created'
    TASK_STARTED = 'task.started'
    TASK_COMPLETED = 'task.completed'
    TASK_FAILED = 'task.failed'
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    INVENTORY_RESERVED = 'inventory.reserved'
    INVENTORY_RELEASED = 'inventory.released'
    NOTIFICATION_SENT = 'notification.sent'


@dataclass
class DomainEvent:
    """
    حدث مجال (Domain Event)

    الأحداث تمثل شيء حدث في الماضي وهي غير قابلة للتغيير
    """
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    causation_id: str | None = None


class EventBus(ABC):
    """
    ناقل الأحداث (Event Bus)

    يوفر الفصل الزمني بين الناشرين والمستهلكين:
    - الناشر لا يعرف من المستهلكين
    - يمكن إضافة مستهلكين جدد دون تعديل الناشر
    - مرونة في معالجة الفشل والإعادة
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) ->None:
        """نشر حدث على الناقل"""
        pass

    @abstractmethod
    async def subscribe(self, event_type: EventType, handler: Callable[[
        DomainEvent], Awaitable[None]]) ->None:
        """الاشتراك في نوع معين من الأحداث"""
        pass


class InMemoryEventBus(EventBus):
    """
    ناقل أحداث في الذاكرة (للتطوير والاختبار)

    في الإنتاج، استخدم RabbitMQ أو Kafka أو AWS EventBridge
    """

    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._event_history: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) ->None:
        """نشر حدث وإشعار جميع المشتركين"""
        self._event_history.append(event)
        logger.info(
            f'📢 Event published: {event.event_type.value} for {event.aggregate_type}#{event.aggregate_id}'
            )
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f'❌ Error in event handler for {event.event_type.value}: {e}'
                    )

    async def subscribe(self, event_type: EventType, handler: Callable[[
        DomainEvent], Awaitable[None]]) ->None:
        """الاشتراك في نوع معين من الأحداث"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f'✅ Subscribed to {event_type.value}')

    def get_event_history(self, aggregate_id: (str | None)=None) ->list[
        DomainEvent]:
        """الحصول على تاريخ الأحداث (للتدقيق والتحليل)"""
        if aggregate_id:
            return [e for e in self._event_history if e.aggregate_id ==
                aggregate_id]
        return self._event_history


@dataclass
class ServiceDefinition:
    """تعريف خدمة في Gateway"""
    service_name: str
    base_url: str
    health_check_path: str = '/health'
    timeout: float = 30.0
    max_retries: int = 3


class APIGateway:
    """
    بوابة API (API Gateway)

    توفر الفصل بين العميل والخدمات الداخلية مع:
    - المصادقة والترخيص
    - تجميع الاستجابات (Response Aggregation)
    - تحويل البروتوكولات
    - التخزين المؤقت (Caching)
    """

    def __init__(self):
        self._services: dict[str, ServiceDefinition] = {}
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    def register_service(self, service: ServiceDefinition) ->None:
        """تسجيل خدمة جديدة"""
        self._services[service.service_name] = service
        logger.info(
            f'✅ Service registered: {service.service_name} at {service.base_url}'
            )

    def get_service(self, service_name: str) ->(ServiceDefinition | None):
        """الحصول على تعريف خدمة"""
        return self._services.get(service_name)

    async def aggregate_response(self, service_calls: list[tuple[str, str,
        dict[str, Any]]]) ->dict[str, Any]:
        """
        تجميع استجابات من خدمات متعددة

        Args:
            service_calls: قائمة من (service_name, endpoint, params)

        Returns:
            استجابة مجمعة من جميع الخدمات
        """
        results = {}
        tasks = []
        for service_name, endpoint, params in service_calls:
            task = self._call_service(service_name, endpoint, params)
            tasks.append((service_name, task))
        for service_name, task in tasks:
            try:
                result = await task
                results[service_name] = result
            except Exception as e:
                logger.error(f'❌ Error calling {service_name}: {e}')
                results[service_name] = {'error': str(e)}
        return results

    async def _call_service(self, service_name: str, endpoint: str, params:
        dict[str, Any]) ->Any:
        """استدعاء خدمة (مثال بسيط)"""
        service = self.get_service(service_name)
        if not service:
            raise ValueError(f'Service {service_name} not found')
        cache_key = f'{service_name}:{endpoint}:{params!s}'
        if cache_key in self._cache:
            cached_data, cached_at = self._cache[cache_key]
            if datetime.now() - cached_at < self._cache_ttl:
                logger.info(f'💾 Cache hit for {cache_key}')
                return cached_data
        result = {'service': service_name, 'endpoint': endpoint, 'params':
            params}
        self._cache[cache_key] = result, datetime.now()
        return result


class CircuitState(Enum):
    """حالات قاطع الدائرة"""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


@dataclass
class CircuitBreakerConfig:
    """تكوين قاطع الدائرة"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    call_timeout: float = 30.0


class CircuitBreaker:
    """
    قاطع الدائرة (Circuit Breaker)

    يمنع الفشل المتسلسل عبر:
    - فتح الدائرة عند فشل متكرر
    - إعادة المحاولة بعد مهلة زمنية
    - استجابة بديلة عند فتح الدائرة
    """

    def __init__(self, name: str, config: (CircuitBreakerConfig | None)=None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.last_state_change = datetime.now()

    async def call(self, func: Callable[..., Awaitable[Any]], *args: Any,
        **kwargs: Any) ->Any:
        """
        استدعاء دالة عبر قاطع الدائرة

        Args:
            func: الدالة المراد استدعاؤها
            *args, **kwargs: معاملات الدالة

        Returns:
            نتيجة الدالة

        Raises:
            Exception: إذا كانت الدائرة مفتوحة أو حدث فشل
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f'🔄 Circuit {self.name} moved to HALF_OPEN')
            else:
                raise Exception(f'Circuit {self.name} is OPEN')
        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=
                self.config.call_timeout)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) ->None:
        """معالجة نجاح الاستدعاء"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info(f'✅ Circuit {self.name} CLOSED')

    def _on_failure(self) ->None:
        """معالجة فشل الاستدعاء"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(f'⚠️ Circuit {self.name} reopened to OPEN')
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f'❌ Circuit {self.name} opened due to failures')

    def _should_attempt_reset(self) ->bool:
        """التحقق مما إذا كان يجب محاولة إعادة التعيين"""
        if not self.last_failure_time:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout


class BulkheadExecutor:
    """
    نمط الحاجز (Bulkhead Pattern)

    يعزل الموارد لمنع استنزاف موارد الخدمة بالكامل:
    - Thread pool محدد لكل خدمة
    - حد أقصى للطلبات المتزامنة
    - قائمة انتظار محدودة
    """

    def __init__(self, name: str, max_concurrent: int=10, queue_size: int=100):
        self.name = name
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._active_tasks = 0

    async def execute(self, func: Callable[..., Awaitable[Any]], *args: Any,
        **kwargs: Any) ->Any:
        """
        تنفيذ دالة عبر الحاجز

        Args:
            func: الدالة المراد تنفيذها
            *args, **kwargs: معاملات الدالة

        Returns:
            نتيجة الدالة
        """
        if self._queue.full():
            raise Exception(f'Bulkhead {self.name} queue is full')
        async with self._semaphore:
            self._active_tasks += 1
            try:
                logger.info(
                    f'🔧 Bulkhead {self.name}: {self._active_tasks}/{self.max_concurrent} active'
                    )
                result = await func(*args, **kwargs)
                return result
            finally:
                self._active_tasks -= 1


class ServiceBoundary:
    """
    حدود الخدمة (Service Boundary)

    يجمع كل أنماط فصل الخدمات في واجهة موحدة:
    - BoundedContext للفصل المجالي
    - EventBus للفصل الزمني
    - APIGateway للفصل بين العميل والخدمات
    - CircuitBreaker للحماية من الفشل
    - BulkheadExecutor لعزل الموارد
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.event_bus = InMemoryEventBus()
        self.api_gateway = APIGateway()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._bulkheads: dict[str, BulkheadExecutor] = {}

    def get_or_create_circuit_breaker(self, name: str, config: (
        CircuitBreakerConfig | None)=None) ->CircuitBreaker:
        """الحصول على أو إنشاء قاطع دائرة"""
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name, config)
        return self._circuit_breakers[name]

    def get_or_create_bulkhead(self, name: str, max_concurrent: int=10,
        queue_size: int=100) ->BulkheadExecutor:
        """الحصول على أو إنشاء حاجز"""
        if name not in self._bulkheads:
            self._bulkheads[name] = BulkheadExecutor(name, max_concurrent,
                queue_size)
        return self._bulkheads[name]


_global_service_boundary: ServiceBoundary | None = None


def get_service_boundary() ->ServiceBoundary:
    """الحصول على مثيل عام من حدود الخدمة"""
    global _global_service_boundary
    if _global_service_boundary is None:
        _global_service_boundary = ServiceBoundary('CogniForge')
    return _global_service_boundary
