# app/boundaries/__init__.py
"""
======================================================================================
 ARCHITECTURAL BOUNDARIES PACKAGE - فصل الاهتمامات عبر الحدود المعمارية
======================================================================================

PURPOSE (الغرض):
  تطبيق مبدأ فصل الاهتمامات (Separation of Concerns) عبر ثلاثة محاور حرجة:
  1. حدود الخدمات (Service Boundaries)
  2. حدود البيانات (Data Boundaries)
  3. حدود السياسات (Policy Boundaries)

ARCHITECTURE (المعمارية):
  - service_boundaries: فصل الخدمات مع تماسك عالي واقتران منخفض
  - data_boundaries: قاعدة بيانات لكل خدمة مع Saga للمعاملات الموزعة
  - policy_boundaries: فصل المصادقة والترخيص والسياسات الأمنية

PRINCIPLES (المبادئ):
  - Single Responsibility: خدمة واحدة، مسؤولية واحدة
  - Loose Coupling: تقليل التبعيات بين المكونات
  - High Cohesion: كل ما يتعلق بمسؤولية واحدة يكون معاً
  - Encapsulation: إخفاء التفاصيل الداخلية
  - Contract-First: تصميم العقود (APIs) أولاً

IMPLEMENTATION DATE: 2025-11-05
VERSION: 1.0.0
======================================================================================
"""

from __future__ import annotations

from app.boundaries.data_boundaries import (
    DataBoundary,
    DatabaseBoundary,
    SagaOrchestrator,
    get_data_boundary,
)
from app.boundaries.policy_boundaries import (
    ComplianceEngine,
    DataGovernanceFramework,
    PolicyBoundary,
    PolicyEngine,
    Principal,
    SecurityPipeline,
    get_policy_boundary,
)
from app.boundaries.service_boundaries import (
    APIGateway,
    BulkheadExecutor,
    CircuitBreaker,
    CircuitBreakerConfig,
    EventBus,
    ServiceBoundary,
    get_service_boundary,
)

__version__ = "1.0.0"

__all__ = [
    # Service Boundaries
    "ServiceBoundary",
    "get_service_boundary",
    "EventBus",
    "APIGateway",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "BulkheadExecutor",
    # Data Boundaries
    "DataBoundary",
    "get_data_boundary",
    "DatabaseBoundary",
    "SagaOrchestrator",
    # Policy Boundaries
    "PolicyBoundary",
    "get_policy_boundary",
    "PolicyEngine",
    "Principal",
    "SecurityPipeline",
    "ComplianceEngine",
    "DataGovernanceFramework",
]
