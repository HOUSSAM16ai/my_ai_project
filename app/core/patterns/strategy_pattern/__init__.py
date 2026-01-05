"""
Strategy Pattern Package
========================

Provides a robust implementation of the Strategy Pattern for runtime algorithm selection.

Exposes:
- Strategy: Abstract base class for strategies
- StrategyRegistry: Registry for managing and executing strategies
"""

from app.core.patterns.strategy_pattern.base import Strategy
from app.core.patterns.strategy_pattern.registry import StrategyRegistry

__all__ = ["Strategy", "StrategyRegistry"]
