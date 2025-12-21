"""Data Boundary Core - Core data access abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.boundaries.data.database import InMemoryDatabaseBoundary
from app.boundaries.data.events import InMemoryEventStore
from app.boundaries.data.saga import SagaOrchestrator


class CommandHandler(ABC):
    """
    معالج الأوامر (Command Handler)

    جانب الكتابة:
    - نموذج الكتابة المُحسّن للاتساق
    - معاملات صارمة
    - نشر أحداث للتغييرات
    """

    @abstractmethod
    async def handle(self, command: dict[str, Any]) -> str:
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
    async def handle(self, query: dict[str, Any]) -> dict[str, Any]:
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
        self._data: dict[str, dict[str, Any]] = {}

    async def query(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """استعلام من نموذج القراءة"""
        results = []
        for _entity_id, entity_data in self._data.items():
            if all(entity_data.get(k) == v for k, v in filters.items()):
                results.append(entity_data)
        return results


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
        self.database = InMemoryDatabaseBoundary(service_name, f'{service_name}_db')
        self.event_store = InMemoryEventStore()
        self.read_models: dict[str, ReadModel] = {}
        self.acl = AntiCorruptionLayer(service_name)

    def create_saga(self, saga_name: str) -> SagaOrchestrator:
        """إنشاء Saga جديد"""
        return SagaOrchestrator(saga_name)


_global_data_boundaries: dict[str, DataBoundary] = {}


def get_data_boundary(service_name: str) -> DataBoundary:
    """الحصول على حدود البيانات لخدمة معينة"""
    if service_name not in _global_data_boundaries:
        _global_data_boundaries[service_name] = DataBoundary(service_name)
    return _global_data_boundaries[service_name]
