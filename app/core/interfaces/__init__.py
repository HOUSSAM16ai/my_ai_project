"""
Core Interfaces - الواجهات النقية
====================================

الواجهات الأساسية للنظام - مفتوحة للتوسع مغلقة للتعديل
Open/Closed Principle Implementation

These interfaces NEVER change - they are the stable contracts.
"""

# Legacy interfaces (kept for backward compatibility)
# New simplified interfaces
from .base import ILifecycle, IPlugin, IService
from .data import ICommand, IQuery, IRepository
from .planner_interface import PlannerInterface
from .processing import IHandler, IProcessor, IValidator
from .repository_interface import RepositoryInterface
from .service_interface import ServiceInterface
from .strategy_interface import StrategyInterface

__all__ = [
    "ICommand",
    "IHandler",
    # New simplified interfaces
    "ILifecycle",
    "IPlugin",
    "IProcessor",
    "IQuery",
    "IRepository",
    "IService",
    "IValidator",
    # Legacy (backward compatibility)
    "PlannerInterface",
    "RepositoryInterface",
    "ServiceInterface",
    "StrategyInterface",
]
