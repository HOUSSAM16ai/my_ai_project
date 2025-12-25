"""
مستودع قاعدي (Base Repository).

يوفر وظائف مشتركة لجميع المستودعات لتطبيق مبدأ DRY.

المعايير:
- Harvard CS50 2025: توثيق عربي شامل
- Berkeley SICP: Abstraction Barriers
- SOLID: Single Responsibility Principle
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseRepository(ABC, Generic[T]):
    """
    مستودع قاعدي لجميع عمليات قاعدة البيانات.
    
    يوفر عمليات CRUD الأساسية ويقلل من التكرار.
    """

    def __init__(self, session: AsyncSession, model: type[T]):
        """
        تهيئة المستودع.
        
        Args:
            session: جلسة قاعدة البيانات
            model: نموذج SQLAlchemy
        """
        self._session = session
        self._model = model
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_by_id(self, id_: int) -> T | None:
        """استرجاع كائن بواسطة المعرف."""
        result = await self._session.execute(
            select(self._model).where(self._model.id == id_)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """استرجاع جميع الكائنات مع الترقيم."""
        result = await self._session.execute(
            select(self._model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        """إنشاء كائن جديد."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        self._logger.info(f"Created {self._model.__name__} with id={obj.id}")
        return obj

    async def update(self, obj: T) -> T:
        """تحديث كائن موجود."""
        await self._session.flush()
        await self._session.refresh(obj)
        self._logger.info(f"Updated {self._model.__name__} with id={obj.id}")
        return obj

    async def delete(self, id_: int) -> bool:
        """حذف كائن بواسطة المعرف."""
        obj = await self.get_by_id(id_)
        if obj:
            await self._session.delete(obj)
            await self._session.flush()
            self._logger.info(f"Deleted {self._model.__name__} with id={id_}")
            return True
        return False

    @abstractmethod
    async def find_by_criteria(self, **criteria: Any) -> list[T]:
        """
        البحث بناءً على معايير محددة.
        
        يجب تنفيذها في الفئات الفرعية حسب الحاجة.
        """
        pass
