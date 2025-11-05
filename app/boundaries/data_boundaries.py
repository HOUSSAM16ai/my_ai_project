# app/boundaries/data_boundaries.py
"""
======================================================================================
 DATA BOUNDARIES - فصل الاهتمامات عبر حدود البيانات
======================================================================================

PURPOSE (الغرض):
  تطبيق مبدأ "قاعدة بيانات لكل خدمة" (Database per Service) مع إدارة موزعة

PATTERNS IMPLEMENTED (الأنماط المطبقة):
  1. Database per Service (قاعدة بيانات لكل خدمة)
  2. Saga Pattern (نمط Saga للمعاملات الموزعة)
  3. Event Sourcing (تخزين الأحداث)
  4. CQRS (فصل القراءة عن الكتابة)
  5. Anti-Corruption Layer (طبقة مكافحة الفساد)

KEY PRINCIPLES (المبادئ الأساسية):
  - كل خدمة تمتلك وتدير قاعدة بياناتها الخاصة حصرياً
  - لا يجوز لخدمة أخرى الوصول المباشر إلى قاعدة بيانات خدمة أخرى
  - استخدام معرّفات خارجية فقط، ليس البيانات الكاملة
  - التناسق النهائي (Eventual Consistency) عبر Sagas
  - تاريخ كامل عبر Event Sourcing

IMPLEMENTATION DATE: 2025-11-05
VERSION: 1.0.0
======================================================================================
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from collections.abc import Awaitable

logger = logging.getLogger(__name__)


# ======================================================================================
# DATABASE PER SERVICE PATTERN
# ======================================================================================


class DatabaseBoundary(ABC):
    """
    حدود قاعدة البيانات (Database Boundary)
    
    كل خدمة تمتلك قاعدة بياناتها الخاصة حصرياً:
    - الوصول: حصري لخدمة واحدة فقط
    - العزل: لا تشارك البيانات مباشرة
    - التواصل: عبر APIs فقط
    """

    def __init__(self, service_name: str, database_name: str):
        self.service_name = service_name
        self.database_name = database_name

    @abstractmethod
    async def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على كيان حسب المعرف"""
        pass

    @abstractmethod
    async def create(self, entity_type: str, data: Dict[str, Any]) -> str:
        """إنشاء كيان جديد"""
        pass

    @abstractmethod
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """تحديث كيان"""
        pass

    @abstractmethod
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """حذف كيان"""
        pass

    def validate_access(self, requesting_service: str) -> bool:
        """
        التحقق من صلاحية الوصول
        
        GOLDEN RULE: فقط الخدمة المالكة يمكنها الوصول
        """
        is_valid = requesting_service == self.service_name
        if not is_valid:
            logger.warning(
                f"❌ Access denied: {requesting_service} tried to access "
                f"{self.service_name} database"
            )
        return is_valid


class InMemoryDatabaseBoundary(DatabaseBoundary):
    """
    تطبيق في الذاكرة لحدود قاعدة البيانات (للتطوير والاختبار)
    
    في الإنتاج، استخدم PostgreSQL أو MongoDB أو DynamoDB
    """

    def __init__(self, service_name: str, database_name: str):
        super().__init__(service_name, database_name)
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {}

    async def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على كيان حسب المعرف"""
        return self._storage.get(entity_type, {}).get(entity_id)

    async def create(self, entity_type: str, data: Dict[str, Any]) -> str:
        """إنشاء كيان جديد"""
        entity_id = str(uuid.uuid4())
        if entity_type not in self._storage:
            self._storage[entity_type] = {}

        self._storage[entity_type][entity_id] = {
            **data,
            "id": entity_id,
            "created_at": datetime.now().isoformat(),
        }
        logger.info(f"✅ Created {entity_type}#{entity_id} in {self.service_name}")
        return entity_id

    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """تحديث كيان"""
        if entity_type not in self._storage or entity_id not in self._storage[entity_type]:
            return False

        self._storage[entity_type][entity_id].update(data)
        self._storage[entity_type][entity_id]["updated_at"] = datetime.now().isoformat()
        logger.info(f"✅ Updated {entity_type}#{entity_id} in {self.service_name}")
        return True

    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """حذف كيان"""
        if entity_type not in self._storage or entity_id not in self._storage[entity_type]:
            return False

        del self._storage[entity_type][entity_id]
        logger.info(f"✅ Deleted {entity_type}#{entity_id} from {self.service_name}")
        return True


# ======================================================================================
# SAGA PATTERN - المعاملات الموزعة
# ======================================================================================


class SagaStepStatus(Enum):
    """حالات خطوة Saga"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"  # تم التعويض


@dataclass
class SagaStep:
    """
    خطوة في Saga
    
    كل خطوة تحتوي على:
    - action: العملية الأساسية
    - compensation: العملية التعويضية (للرجوع عند الفشل)
    """

    step_id: str
    step_name: str
    action: Callable[..., Awaitable[Any]]
    compensation: Callable[..., Awaitable[Any]]
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SagaOrchestrator:
    """
    منسق Saga (Saga Orchestrator)
    
    يدير تنفيذ Saga مع معاملات التعويض عند الفشل:
    1. تنفيذ الخطوات بالترتيب
    2. عند فشل خطوة، تنفيذ التعويضات بالعكس
    3. ضمان التناسق النهائي
    
    مثال: إنشاء طلب
    1. إنشاء طلب (PENDING) → نجح → OrderCreated
    2. حجز المخزون → نجح → InventoryReserved
    3. معالجة الدفع → فشل → تعويض: ReleaseInventory + CancelOrder
    """

    def __init__(self, saga_name: str):
        self.saga_name = saga_name
        self.steps: List[SagaStep] = []
        self.current_step_index = 0
        self.saga_id = str(uuid.uuid4())
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def add_step(
        self,
        step_name: str,
        action: Callable[..., Awaitable[Any]],
        compensation: Callable[..., Awaitable[Any]],
    ) -> None:
        """إضافة خطوة جديدة إلى Saga"""
        step_id = f"{self.saga_id}:{len(self.steps)}"
        step = SagaStep(
            step_id=step_id, step_name=step_name, action=action, compensation=compensation
        )
        self.steps.append(step)
        logger.info(f"➕ Added step {step_name} to saga {self.saga_name}")

    async def execute(self) -> bool:
        """
        تنفيذ Saga
        
        Returns:
            True إذا نجحت جميع الخطوات، False إذا حدث فشل
        """
        self.started_at = datetime.now()
        logger.info(f"🚀 Starting saga {self.saga_name} ({self.saga_id})")

        # تنفيذ الخطوات بالترتيب
        for i, step in enumerate(self.steps):
            self.current_step_index = i
            step.status = SagaStepStatus.RUNNING
            step.started_at = datetime.now()

            try:
                logger.info(f"▶️ Executing step {i + 1}/{len(self.steps)}: {step.step_name}")
                step.result = await step.action()
                step.status = SagaStepStatus.COMPLETED
                step.completed_at = datetime.now()
                logger.info(f"✅ Step {step.step_name} completed")
            except Exception as e:
                step.status = SagaStepStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.now()
                logger.error(f"❌ Step {step.step_name} failed: {e}")

                # تنفيذ التعويضات بالعكس
                await self._compensate(i)
                return False

        self.completed_at = datetime.now()
        logger.info(f"✅ Saga {self.saga_name} completed successfully")
        return True

    async def _compensate(self, failed_step_index: int) -> None:
        """
        تنفيذ معاملات التعويض (Compensating Transactions)
        
        Args:
            failed_step_index: فهرس الخطوة التي فشلت
        """
        logger.warning(f"🔄 Starting compensation for saga {self.saga_name}")

        # تنفيذ التعويضات بالعكس للخطوات المكتملة فقط
        for i in range(failed_step_index - 1, -1, -1):
            step = self.steps[i]
            if step.status == SagaStepStatus.COMPLETED:
                try:
                    logger.info(f"↩️ Compensating step: {step.step_name}")
                    await step.compensation()
                    step.status = SagaStepStatus.COMPENSATED
                    logger.info(f"✅ Compensated step: {step.step_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to compensate step {step.step_name}: {e}")
                    # في الإنتاج، أرسل إلى Dead Letter Queue للمراجعة اليدوية

    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة Saga"""
        return {
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_step": self.current_step_index,
            "total_steps": len(self.steps),
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "error": step.error,
                }
                for step in self.steps
            ],
        }


# ======================================================================================
# EVENT SOURCING - تخزين الأحداث
# ======================================================================================


@dataclass
class StoredEvent:
    """
    حدث مخزّن (Stored Event)
    
    بدلاً من تخزين الحالة النهائية، نخزن جميع الأحداث التي أدت إليها
    """

    event_id: str
    aggregate_id: str  # معرف الكيان
    aggregate_type: str  # نوع الكيان
    event_type: str
    event_data: Dict[str, Any]
    occurred_at: datetime
    version: int  # إصدار الكيان (للتزامن التفاؤلي)


class EventStore(ABC):
    """
    مخزن الأحداث (Event Store)
    
    يخزن جميع الأحداث ويسمح بإعادة بناء الحالة من الأحداث
    """

    @abstractmethod
    async def append_event(self, event: StoredEvent) -> None:
        """إضافة حدث جديد"""
        pass

    @abstractmethod
    async def get_events(
        self, aggregate_id: str, from_version: int = 0
    ) -> List[StoredEvent]:
        """الحصول على أحداث كيان معين"""
        pass

    @abstractmethod
    async def get_current_version(self, aggregate_id: str) -> int:
        """الحصول على الإصدار الحالي لكيان"""
        pass


class InMemoryEventStore(EventStore):
    """تطبيق في الذاكرة لمخزن الأحداث (للتطوير والاختبار)"""

    def __init__(self):
        self._events: List[StoredEvent] = []
        self._versions: Dict[str, int] = {}

    async def append_event(self, event: StoredEvent) -> None:
        """إضافة حدث جديد"""
        self._events.append(event)
        self._versions[event.aggregate_id] = event.version
        logger.info(
            f"📝 Event stored: {event.event_type} for {event.aggregate_type}#{event.aggregate_id} v{event.version}"
        )

    async def get_events(
        self, aggregate_id: str, from_version: int = 0
    ) -> List[StoredEvent]:
        """الحصول على أحداث كيان معين"""
        return [
            e
            for e in self._events
            if e.aggregate_id == aggregate_id and e.version >= from_version
        ]

    async def get_current_version(self, aggregate_id: str) -> int:
        """الحصول على الإصدار الحالي لكيان"""
        return self._versions.get(aggregate_id, 0)


class EventSourcedAggregate:
    """
    كيان مُحدّث من الأحداث (Event Sourced Aggregate)
    
    الحالة الحالية = تطبيق جميع الأحداث بالترتيب
    """

    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0
        self._changes: List[StoredEvent] = []

    def apply_event(self, event: StoredEvent) -> None:
        """
        تطبيق حدث على الكيان
        
        يجب تنفيذ في الفئات الوارثة لتحديث الحالة
        """
        self.version = event.version
        self._changes.append(event)

    async def load_from_history(self, event_store: EventStore) -> None:
        """
        إعادة بناء الحالة من الأحداث
        
        يقرأ جميع الأحداث ويطبقها بالترتيب
        """
        events = await event_store.get_events(self.aggregate_id)
        for event in events:
            self.apply_event(event)
        logger.info(
            f"📖 Loaded {len(events)} events for {self.aggregate_type}#{self.aggregate_id}"
        )

    async def commit(self, event_store: EventStore) -> None:
        """
        حفظ التغييرات إلى مخزن الأحداث
        """
        for event in self._changes:
            await event_store.append_event(event)
        self._changes.clear()


# ======================================================================================
# CQRS - فصل القراءة عن الكتابة
# ======================================================================================


class CommandHandler(ABC):
    """
    معالج الأوامر (Command Handler)
    
    جانب الكتابة:
    - نموذج الكتابة المُحسّن للاتساق
    - معاملات صارمة
    - نشر أحداث للتغييرات
    """

    @abstractmethod
    async def handle(self, command: Dict[str, Any]) -> str:
        """
        معالجة أمر
        
        Returns:
            معرف الكيان المُنشأ أو المُحدّث
        """
        pass


class QueryHandler(ABC):
    """
    معالج الاستعلامات (Query Handler)
    
    جانب القراءة:
    - نماذج قراءة مُحسّنة للأداء (Denormalized Views)
    - تحديث لا متزامن من الأحداث
    - يمكن أن تكون متأخرة قليلاً (Eventually Consistent)
    """

    @abstractmethod
    async def handle(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        معالجة استعلام
        
        Returns:
            نتيجة الاستعلام
        """
        pass


class ReadModel:
    """
    نموذج القراءة (Read Model)
    
    نموذج منسوخ ومُحسّن للقراءة السريعة:
    - Denormalized (غير مُعياري)
    - مفهرس بشكل مكثف
    - يُحدّث من الأحداث بشكل لا متزامن
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._data: Dict[str, Dict[str, Any]] = {}

    async def update_from_event(self, event: StoredEvent) -> None:
        """تحديث نموذج القراءة من حدث"""
        # تنفيذ محدد في الفئات الوارثة
        pass

    async def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استعلام من نموذج القراءة"""
        # بحث بسيط للمثال
        results = []
        for entity_id, entity_data in self._data.items():
            if all(entity_data.get(k) == v for k, v in filters.items()):
                results.append(entity_data)
        return results


# ======================================================================================
# ANTI-CORRUPTION LAYER - طبقة مكافحة الفساد
# ======================================================================================


class AntiCorruptionLayer:
    """
    طبقة مكافحة الفساد (Anti-Corruption Layer)
    
    تحمي نموذجك من النماذج الخارجية:
    - ترجمة النماذج
    - تحويل البيانات
    - تطبيع الأخطاء
    - إخفاء التعقيد
    """

    def __init__(self, service_name: str):
        self.service_name = service_name

    def to_domain_model(self, external_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تحويل البيانات الخارجية إلى نموذج النطاق الداخلي
        
        مثال:
        Legacy: {CUST_ID: "123", F_NAME: "أحمد", L_NAME: "محمد"}
        Domain: {id: "123", full_name: "أحمد محمد"}
        """
        # تنفيذ محدد في الفئات الوارثة
        return external_data

    def from_domain_model(self, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تحويل نموذج النطاق الداخلي إلى البيانات الخارجية
        """
        # تنفيذ محدد في الفئات الوارثة
        return domain_data

    def normalize_error(self, external_error: Exception) -> Exception:
        """
        تطبيع الأخطاء الخارجية إلى أخطاء داخلية
        """
        # تحويل الأخطاء الخارجية إلى أخطاء نطاق
        return external_error


# ======================================================================================
# DATA BOUNDARY ABSTRACTION
# ======================================================================================


class DataBoundary:
    """
    حدود البيانات (Data Boundary)
    
    يجمع كل أنماط فصل البيانات في واجهة موحدة:
    - DatabaseBoundary لعزل قواعد البيانات
    - SagaOrchestrator للمعاملات الموزعة
    - EventStore لتخزين الأحداث
    - CQRS لفصل القراءة عن الكتابة
    - AntiCorruptionLayer للحماية من النماذج الخارجية
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.database = InMemoryDatabaseBoundary(service_name, f"{service_name}_db")
        self.event_store = InMemoryEventStore()
        self.read_models: Dict[str, ReadModel] = {}
        self.acl = AntiCorruptionLayer(service_name)

    def create_saga(self, saga_name: str) -> SagaOrchestrator:
        """إنشاء Saga جديد"""
        return SagaOrchestrator(saga_name)

    def get_or_create_read_model(self, model_name: str) -> ReadModel:
        """الحصول على أو إنشاء نموذج قراءة"""
        if model_name not in self.read_models:
            self.read_models[model_name] = ReadModel(model_name)
        return self.read_models[model_name]


# ======================================================================================
# GLOBAL INSTANCE (اختياري)
# ======================================================================================

_global_data_boundaries: Dict[str, DataBoundary] = {}


def get_data_boundary(service_name: str) -> DataBoundary:
    """الحصول على حدود البيانات لخدمة معينة"""
    if service_name not in _global_data_boundaries:
        _global_data_boundaries[service_name] = DataBoundary(service_name)
    return _global_data_boundaries[service_name]
