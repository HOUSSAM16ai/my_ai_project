# ======================================================================================
#  MAESTRO ADAPTER (v2.5.0 • "BRIDGE-FUSION-OMNI")
#  File: app/services/maestro/__init__.py
# ======================================================================================
#  PURPOSE:
#    Public exports for the Maestro Adapter.
#    Implementation moved to adapter.py to separate concerns.
# ======================================================================================

from app.services.maestro.adapter import (
    __version__,
    diagnostics,
    ensure_adapter_ready,
    generation_service,
)

__all__ = [
    "__version__",
    "diagnostics",
    "ensure_adapter_ready",
    "generation_service",
]
