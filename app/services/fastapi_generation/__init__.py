"""
FastAPI Generation Service - Hexagonal Architecture
===================================================

Refactored from monolithic 629-line file to modular architecture.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (generation_manager)
- infrastructure/: External adapters (llm_adapter, model_selector, etc.)
- facade.py: Backward-compatible interface

Reduction: 629 lines → ~60 lines shim (90.5% reduction)
"""
from __future__ import annotations

import json
from typing import Any, Callable

from app.models import Task

from .domain.models import (
    OrchestratorConfig,
    OrchestratorTelemetry,
    StepState,
)
from .facade import MaestroGenerationService

# Singleton instance
_generation_service_singleton: MaestroGenerationService | None = None


def get_generation_service() -> MaestroGenerationService:
    """Get singleton instance of generation service."""
    global _generation_service_singleton
    if _generation_service_singleton is None:
        _generation_service_singleton = MaestroGenerationService()
    return _generation_service_singleton


# Convenience functions for backward compatibility
def forge_new_code(*args, **kwargs) -> dict[str, Any]:
    """Generate new code."""
    return get_generation_service().forge_new_code(*args, **kwargs)


def generate_json(*args, **kwargs) -> dict[str, Any]:
    """Generate JSON response."""
    return get_generation_service().generate_json(*args, **kwargs)


def generate_comprehensive_response(*args, **kwargs) -> dict[str, Any]:
    """Generate comprehensive response."""
    return get_generation_service().generate_comprehensive_response(*args, **kwargs)


def execute_task(task: Task, model: str | None = None) -> None:
    """Execute task."""
    return get_generation_service().execute_task(task, model=model)


def diagnostics() -> dict[str, Any]:
    """Get service diagnostics."""
    return get_generation_service().diagnostics()


def register_post_finalize_hook(func: Callable[[Any], None]) -> bool:
    """Register post-finalization hook."""
    svc = get_generation_service()
    svc.post_finalize_hook = func
    return True


# Module-level singleton for backward compatibility
generation_service = get_generation_service()

__all__ = [
    # Main service
    "MaestroGenerationService",
    "get_generation_service",
    "generation_service",
    # Domain models
    "OrchestratorTelemetry",
    "StepState",
    "OrchestratorConfig",
    # Convenience functions
    "diagnostics",
    "execute_task",
    "forge_new_code",
    "generate_comprehensive_response",
    "generate_json",
    "register_post_finalize_hook",
]

__version__ = "18.1.0-refactored"

if __name__ == "__main__":
    svc = generation_service
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
