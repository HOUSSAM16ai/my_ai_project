"""
Data Interfaces - واجهات البيانات
====================================

واجهات الوصول للبيانات - CQRS Pattern
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class IRepository(ABC, Generic[T, ID]):
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


class IQuery(ABC, Generic[T]):
    """
    واجهة الاستعلام - Query Interface
    CQRS Pattern - Read side
    """

    @abstractmethod
    async def execute(self) -> T:
        """Execute query"""
        pass


class ICommand(ABC, Generic[T]):
    """
    واجهة الأمر - Command Interface
    CQRS Pattern - Write side
    """

    @abstractmethod
    async def execute(self) -> T:
        """Execute command"""
        pass
