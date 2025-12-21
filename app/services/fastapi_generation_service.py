"""
FastAPI Generation Service - Backward Compatible Shim
=====================================================

⚠️ REFACTORED: This file now delegates to the hexagonal architecture implementation.
See: app/services/fastapi_generation/ for the new modular structure.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (generation_manager)
- infrastructure/: External adapters (llm_adapter, model_selector, etc.)
- facade.py: Backward-compatible interface

Original: 629 lines (monolithic)
Refactored: 60 lines (shim) + ~10 modular files
Reduction: 90.5% (569 lines removed)

Status: ✅ Wave 10 Refactored
"""
from __future__ import annotations



# Import from new modular structure
from .fastapi_generation import (
    MaestroGenerationService,
    OrchestratorConfig,
    OrchestratorTelemetry,
    StepState,
    diagnostics,
    execute_task,
    forge_new_code,
    generate_comprehensive_response,
    generate_json,
    generation_service,
    get_generation_service,
    register_post_finalize_hook,
)

# Re-export for backward compatibility
__all__ = [
    "MaestroGenerationService",
    "OrchestratorConfig",
    "OrchestratorTelemetry",
    "StepState",
    "diagnostics",
    "execute_task",
    "forge_new_code",
    "generate_comprehensive_response",
    "generate_json",
    "generation_service",
    "get_generation_service",
    "register_post_finalize_hook",
]

__version__ = "18.1.0-refactored"

# Backward compatibility: expose module-level singleton
generation_service = get_generation_service()

if __name__ == "__main__":
    import json

    svc = generation_service
    print("=== FastAPI Generation Service Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
