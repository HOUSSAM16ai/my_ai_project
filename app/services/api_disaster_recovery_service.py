# app/services/api_disaster_recovery_service.py
"""
🚀 SUPERHUMAN DISASTER RECOVERY & ON-CALL SERVICE - LEGACY COMPATIBILITY SHIM
============================================================================

نظام التعافي من الكوارث وإدارة الحوادث الخارق
This file maintains backward compatibility by delegating to the refactored
hexagonal architecture in app/services/disaster_recovery/

Original file: 696 lines
Refactored: Delegates to disaster_recovery/ module

SOLID PRINCIPLES APPLIED:
  - Single Responsibility: Each component has one clear purpose
  - Open/Closed: Open for extension via ports/adapters
  - Liskov Substitution: All implementations are interchangeable
  - Interface Segregation: Small focused protocols
  - Dependency Inversion: Depends on abstractions (ports)

For new code, import from: app.services.disaster_recovery
This shim exists for backward compatibility only.
"""

from __future__ import annotations

# Re-export everything from the refactored hexagonal architecture
from app.services.disaster_recovery import (
    # Domain models
    IncidentSeverity,
    IncidentStatus,
    OnCallRole,
    RecoveryStrategy,
    NotificationChannel,
    Incident,
    OnCallSchedule,
    EscalationPolicy,
    DisasterRecoveryPlan,
    BackupMetadata,
    PostIncidentReview,
    # Facade services
    DisasterRecoveryService,
    OnCallIncidentService,
    get_disaster_recovery_service,
    get_oncall_incident_service,
)

__all__ = [
    # Enums
    "IncidentSeverity",
    "IncidentStatus",
    "OnCallRole",
    "RecoveryStrategy",
    "NotificationChannel",
    # Models
    "Incident",
    "OnCallSchedule",
    "EscalationPolicy",
    "DisasterRecoveryPlan",
    "BackupMetadata",
    "PostIncidentReview",
    # Services
    "DisasterRecoveryService",
    "OnCallIncidentService",
    "get_disaster_recovery_service",
    "get_oncall_incident_service",
]
