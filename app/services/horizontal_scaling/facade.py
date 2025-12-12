"""
Horizontal Scaling Facade
=========================

Main entry point for the service.
Combines Domain, Application, and Infrastructure layers.
"""
from __future__ import annotations

from .application.manager import HorizontalScalingManager
from .application.chaos_monkey import ChaosMonkey

# Singleton instance
_manager_instance: HorizontalScalingManager | None = None

def get_scaling_orchestrator() -> HorizontalScalingManager:
    """Get the singleton instance of the Horizontal Scaling Manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = HorizontalScalingManager()
    return _manager_instance

def get_chaos_monkey() -> ChaosMonkey:
    """Get a new Chaos Monkey instance attached to the global orchestrator."""
    return ChaosMonkey(get_scaling_orchestrator())
