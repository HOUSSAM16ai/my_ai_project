"""
Base Interfaces - الواجهات الأساسية
======================================

الواجهات الأساسية التي لا تتغير أبداً
These are the sacred contracts - NEVER modify them.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ILifecycle(ABC):
    """واجهة دورة الحياة - Lifecycle Interface"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the component"""
        pass


class IService(ILifecycle):
    """
    واجهة الخدمة الأساسية
    Base Service Interface

    All services MUST implement this interface.
    مبدأ: مفتوح للتوسع، مغلق للتعديل
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Service unique name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Service version"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        pass


class IPlugin(IService):
    """
    واجهة الإضافة
    Plugin Interface

    Plugins extend the system without modifying core code.
    """

    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """Type of plugin (service, processor, etc.)"""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> list[str]:
        """List of required dependencies"""
        pass

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin"""
        pass
