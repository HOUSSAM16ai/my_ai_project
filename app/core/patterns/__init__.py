"""
Design patterns implementation for the application.

This module provides reusable design pattern implementations:
- Builder pattern for fluent object construction
- Strategy pattern for algorithm selection
"""

from app.core.patterns.builder import FluentBuilder
from app.core.patterns.strategy import Strategy, StrategyRegistry

__all__ = ["FluentBuilder", "Strategy", "StrategyRegistry"]
