"""
Processing Interfaces - واجهات المعالجة
==========================================

واجهات معالجة البيانات والطلبات
"""

from abc import ABC, abstractmethod
from typing import TypeVar

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')


class IProcessor[TInput, TOutput](ABC):
    """
    واجهة المعالج
    Processor Interface - Generic pattern
    """

    @abstractmethod
    async def process(self, input: TInput) -> TOutput:
        """Process input and return output"""
        pass


class IHandler[TInput, TOutput](ABC):
    """
    واجهة المعالج مع Chain of Responsibility
    Handler Interface - Can be chained
    """

    @abstractmethod
    async def handle(self, input: TInput) -> TOutput:
        """Handle input"""
        pass

    @abstractmethod
    def set_next(self, handler: 'IHandler') -> 'IHandler':
        """Set next handler in chain"""
        pass


class IValidator[TInput](ABC):
    """
    واجهة المدقق
    Validator Interface
    """

    @abstractmethod
    async def validate(self, input: TInput) -> bool:
        """Validate input"""
        pass

    @abstractmethod
    def get_errors(self) -> list[str]:
        """Get validation errors"""
        pass
