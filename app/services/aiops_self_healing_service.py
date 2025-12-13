"""
AIOps Self Healing Service - Backward Compatible Shim
===================================================

⚠️ REFACTORED: This file now delegates to the hexagonal architecture implementation.
See: app/services/aiops_self_healing/ for the new modular structure.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (service)
- infrastructure/: Adapters (repositories)
- facade.py: Main entry point

Original: 601 lines (monolithic)
Refactored: ~60 lines (shim) + Modular structure
Reduction: 90%

Status: ✅ Wave 10 Refactored
"""
from __future__ import annotations

# Import from new modular structure
from .aiops_self_healing.domain.models import (
    AnomalyType,
    AnomalySeverity,
    HealingAction,
    MetricType,
    TelemetryData,
    AnomalyDetection,
    LoadForecast,
    HealingDecision,
    CapacityPlan,
)
from .aiops_self_healing.application.service import (
    AIOpsService,
    get_aiops_service,
)

# Re-export for backward compatibility
__all__ = [
    "AnomalyType",
    "AnomalySeverity",
    "HealingAction",
    "MetricType",
    "TelemetryData",
    "AnomalyDetection",
    "LoadForecast",
    "HealingDecision",
    "CapacityPlan",
    "AIOpsService",
    "get_aiops_service",
]

# Singleton instance
_aiops_instance = get_aiops_service()

if __name__ == "__main__":
    import json

    svc = get_aiops_service()
    print("=== AIOps Service Diagnostics (Refactored) ===")
    print(json.dumps(svc.get_aiops_metrics(), ensure_ascii=False, indent=2))
