from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from enum import Enum


class FallbackLevel(Enum):
    """Fallback chain levels"""

    PRIMARY = "primary"  # Best data source
    REPLICA = "replica"  # Read replica
    DISTRIBUTED_CACHE = "distributed_cache"  # Redis cluster
    LOCAL_CACHE = "local_cache"  # In-memory cache
    BACKUP_SERVICE = "backup_service"  # Alternative provider
    DEFAULT = "default"  # Always succeeds


class FallbackChain:
    """
    Multi-Level Fallback Chain

    Levels:
    1. Primary Database -> Best data
    2. Read Replica -> Milliseconds stale
    3. Distributed Cache -> Minutes stale
    4. Local Cache -> Hours stale
    5. Backup Service -> Alternative provider
    6. Default Data -> Always succeeds
    """

    def __init__(self):
        self.handlers: dict[FallbackLevel, Callable] = {}
        self._lock = threading.RLock()

    def register_handler(self, level: FallbackLevel, handler: Callable) -> None:
        """Register a fallback handler"""
        with self._lock:
            self.handlers[level] = handler

    def execute(self, *args, **kwargs) -> tuple[object, FallbackLevel, bool]:
        """
        Execute with fallback chain

        Returns:
            (result, level_used, degraded)
        """
        levels = [
            FallbackLevel.PRIMARY,
            FallbackLevel.REPLICA,
            FallbackLevel.DISTRIBUTED_CACHE,
            FallbackLevel.LOCAL_CACHE,
            FallbackLevel.BACKUP_SERVICE,
            FallbackLevel.DEFAULT,
        ]

        for level in levels:
            if level not in self.handlers:
                continue

            try:
                result = self.handlers[level](*args, **kwargs)
                degraded = level != FallbackLevel.PRIMARY
                return result, level, degraded
            except Exception as e:
                # Log and continue to next level
                logging.getLogger(__name__).warning(f"Fallback level {level.value} failed: {e}")
                continue

        # If all fail, raise
        raise Exception("All fallback levels exhausted")
