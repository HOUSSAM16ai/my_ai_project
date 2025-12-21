"""
======================================================================================
 DATA BOUNDARIES - فصل الاهتمامات عبر حدود البيانات
======================================================================================

PURPOSE (الغرض):
  تطبيق مبدأ "قاعدة بيانات لكل خدمة" (Database per Service) مع إدارة موزعة

PATTERNS IMPLEMENTED (الأنماط المطبقة):
  1. Database per Service (قاعدة بيانات لكل خدمة)
  2. Saga Pattern (نمط Saga للمعاملات الموزعة)
  3. Event Sourcing (تخزين الأحداث)
  4. CQRS (فصل القراءة عن الكتابة)
  5. Anti-Corruption Layer (طبقة مكافحة الفساد)

KEY PRINCIPLES (المبادئ الأساسية):
  - كل خدمة تمتلك وتدير قاعدة بياناتها الخاصة حصرياً
  - لا يجوز لخدمة أخرى الوصول المباشر إلى قاعدة بيانات خدمة أخرى
  - استخدام معرّفات خارجية فقط، ليس البيانات الكاملة
  - التناسق النهائي (Eventual Consistency) عبر Sagas
  - تاريخ كامل عبر Event Sourcing

IMPLEMENTATION DATE: 2025-11-05
VERSION: 1.0.0
======================================================================================
"""
from __future__ import annotations

# Re-export from decomposed modules to maintain backward compatibility
from app.boundaries.data.database import DatabaseBoundary, InMemoryDatabaseBoundary
from app.boundaries.data.events import (
    EventStore, InMemoryEventStore, StoredEvent, EventSourcedAggregate
)
from app.boundaries.data.saga import SagaOrchestrator, SagaStep, SagaStepStatus
from app.boundaries.data.core import (
    CommandHandler, QueryHandler, ReadModel, AntiCorruptionLayer,
    DataBoundary, get_data_boundary
)

__all__ = [
    "DatabaseBoundary",
    "InMemoryDatabaseBoundary",
    "SagaOrchestrator",
    "SagaStep",
    "SagaStepStatus",
    "EventStore",
    "InMemoryEventStore",
    "StoredEvent",
    "EventSourcedAggregate",
    "CommandHandler",
    "QueryHandler",
    "ReadModel",
    "AntiCorruptionLayer",
    "DataBoundary",
    "get_data_boundary",
]
