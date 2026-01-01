"""
Boundaries Module - Architectural Boundaries Implementation
============================================================

This module implements Clean Architecture boundaries for separation of concerns.
فصل الاهتمامات عبر الحدود المعمارية

Module Structure:
- service_boundaries: Service boundary implementations
- data_boundaries: Data boundary implementations  
- policy_boundaries: Policy boundary implementations
"""

from app.boundaries.data_boundaries import (
    DataBoundary,
    EventSourcedAggregate,
    InMemoryEventStore,
    StoredEvent,
    get_data_boundary,
)
from app.boundaries.policy_boundaries import (
    ComplianceRegulation,
    ComplianceRule,
    DataClassification,
    Effect,
    Policy,
    PolicyBoundary,
    PolicyRule,
    Principal,
    get_policy_boundary,
)
from app.boundaries.service_boundaries import (
    CircuitBreakerConfig,
    DomainEvent,
    EventType,
    ServiceBoundary,
    ServiceDefinition,
    get_service_boundary,
)

__all__ = [
    # Service Boundaries
    "CircuitBreakerConfig",
    "DomainEvent",
    "EventType",
    "ServiceBoundary",
    "ServiceDefinition",
    "get_service_boundary",
    # Data Boundaries
    "DataBoundary",
    "EventSourcedAggregate",
    "InMemoryEventStore",
    "StoredEvent",
    "get_data_boundary",
    # Policy Boundaries
    "ComplianceRegulation",
    "ComplianceRule",
    "DataClassification",
    "Effect",
    "Policy",
    "PolicyBoundary",
    "PolicyRule",
    "Principal",
    "get_policy_boundary",
]
