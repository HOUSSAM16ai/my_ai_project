"""
Core Interfaces - الواجهات النقية
====================================

الواجهات الأساسية للنظام - مفتوحة للتوسع مغلقة للتعديل
Open/Closed Principle Implementation

These interfaces NEVER change - they are the stable contracts.
"""

# Legacy interfaces (kept for backward compatibility)
from .planner_interface import PlannerInterface
from .repository_interface import RepositoryInterface
from .service_interface import ServiceInterface
from .strategy_interface import StrategyInterface

# New simplified interfaces
from .base import ILifecycle, IPlugin, IService
from .data import ICommand, IQuery, IRepository
from .processing import IHandler, IProcessor, IValidator

__all__ = [
    # Legacy (backward compatibility)
    "PlannerInterface",
    "RepositoryInterface",
    "ServiceInterface",
    "StrategyInterface",
    # New simplified interfaces
    "ILifecycle",
    "IPlugin",
    "IService",
    "ICommand",
    "IQuery",
    "IRepository",
    "IHandler",
    "IProcessor",
    "IValidator",
]
