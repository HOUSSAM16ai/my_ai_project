"""
Supernatural Failure Planning (Circuit Breaker & Fallback).
Wraps strategy execution to ensure reliability even if the primary strategy fails.
"""
from __future__ import annotations

import logging

from .schemas import MissionPlanSchema, PlanningContext
from .strategies.base_strategy import BasePlanningStrategy
from .strategies.linear_strategy import LinearStrategy

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Simple Circuit Breaker implementation.
    """

    def __init__(self, failure_threshold: int=3, reset_timeout: int=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = 'CLOSED'

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning('Circuit Breaker OPENED due to failures.')

    def record_success(self):
        self.failures = 0
        self.state = 'CLOSED'

    def allow_request(self) ->bool:
        return self.state != 'OPEN'


class ResilientPlanner:
    """
    Wrapper ensuring execution success via fallbacks.
    """

    def __init__(self, primary_strategy: BasePlanningStrategy,
        fallback_strategy: BasePlanningStrategy=None):
        self.primary = primary_strategy
        self.fallback = fallback_strategy or LinearStrategy()
        self.breaker = CircuitBreaker()

    def generate_safely(self, objective: str, context: (PlanningContext |
        None)=None) ->MissionPlanSchema:
        if self.breaker.allow_request():
            try:
                plan = self.primary.generate(objective, context)
                self.breaker.record_success()
                return plan
            except Exception as e:
                logger.error(
                    f'Primary strategy {self.primary.name} failed: {e}')
                self.breaker.record_failure()
        logger.info(f'Engaging fallback strategy: {self.fallback.name}')
        return self.fallback.generate(objective, context)
