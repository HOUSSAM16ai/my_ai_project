"""Data Boundary Database - Database access layer."""
from __future__ import annotations

from typing import Any

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

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
    async def get_by_id(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        """الحصول على كيان حسب المعرف"""
        pass

    @abstractmethod
    async def create(self, entity_type: str, data: dict[str, Any]) -> str:
        """إنشاء كيان جديد"""
        pass

    @abstractmethod
    async def update(self, entity_type: str, entity_id: str, data: dict[str, Any]) -> bool:
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
                f'❌ Access denied: {requesting_service} tried to access {self.service_name} database'
            )
        return is_valid

class InMemoryDatabaseBoundary(DatabaseBoundary):
    """
    تطبيق في الذاكرة لحدود قاعدة البيانات (للتطوير والاختبار)

    في الإنتاج، استخدم PostgreSQL أو MongoDB أو DynamoDB
    """

    def __init__(self, service_name: str, database_name: str):
        super().__init__(service_name, database_name)
        self._storage: dict[str, dict[str, dict[str, Any]]] = {}

    async def get_by_id(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        """الحصول على كيان حسب المعرف"""
        return self._storage.get(entity_type, {}).get(entity_id)

    async def create(self, entity_type: str, data: dict[str, Any]) -> str:
        """إنشاء كيان جديد"""
        entity_id = str(uuid.uuid4())
        if entity_type not in self._storage:
            self._storage[entity_type] = {}
        self._storage[entity_type][entity_id] = {
            **data,
            'id': entity_id,
            'created_at': datetime.now().isoformat()
        }
        logger.info(f'✅ Created {entity_type}#{entity_id} in {self.service_name}')
        return entity_id

    async def update(self, entity_type: str, entity_id: str, data: dict[str, Any]) -> bool:
        """تحديث كيان"""
        if entity_type not in self._storage or entity_id not in self._storage[entity_type]:
            return False
        self._storage[entity_type][entity_id].update(data)
        self._storage[entity_type][entity_id]['updated_at'] = datetime.now().isoformat()
        logger.info(f'✅ Updated {entity_type}#{entity_id} in {self.service_name}')
        return True

    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """حذف كيان"""
        if entity_type not in self._storage or entity_id not in self._storage[entity_type]:
            return False
        del self._storage[entity_type][entity_id]
        logger.info(f'✅ Deleted {entity_type}#{entity_id} from {self.service_name}')
        return True
