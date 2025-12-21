"""
Data Interfaces - واجهات البيانات
====================================

واجهات الوصول للبيانات - CQRS Pattern
"""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar('T')
ID = TypeVar('ID')


class IRepository[T, ID](ABC):
    """
    واجهة المستودع
    Repository Interface - Generic pattern
    """

    @abstractmethod
    async def get(self, id: ID) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:  # noqa: unused variable
        """Save entity"""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete entity"""
        pass


class IQuery[T](ABC):
    """
    واجهة الاستعلام - Query Interface
    CQRS Pattern - Read side
    """

    @abstractmethod
    async def execute(self) -> T:
        """Execute query"""
        pass


class ICommand[T](ABC):
    """
    واجهة الأمر - Command Interface
    CQRS Pattern - Write side
    """

    @abstractmethod
    async def execute(self) -> T:
        """Execute command"""
        pass
