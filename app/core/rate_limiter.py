# app/core/rate_limiter.py
"""
TOOL RATE LIMITER
=================
Prevents abuse of tool execution by limiting calls per user per time window.
Thread-safe implementation with cooldown support.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    max_calls: int = 20  # Max calls per window
    window_seconds: float = 60  # Time window in seconds
    cooldown_seconds: float = 5  # Cooldown after limit hit


class ToolRateLimiter:
    """Thread-safe rate limiter for tool execution."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._cooldowns: dict[str, float] = {}
        self._lock = threading.Lock()

    def _cleanup_old_calls(self, key: str, now: float):
        """Remove calls outside the time window."""
        cutoff = now - self.config.window_seconds
        self._calls[key] = [t for t in self._calls[key] if t > cutoff]

    def check(self, user_id: int, tool_name: str) -> tuple[bool, str]:
        """
        Check if a tool call is allowed.

        Returns:
            (allowed: bool, reason: str)
        """
        key = f"{user_id}:{tool_name}"
        now = time.time()

        with self._lock:
            # Check cooldown
            if key in self._cooldowns:
                cooldown_end = self._cooldowns[key]
                if now < cooldown_end:
                    remaining = int(cooldown_end - now)
                    return False, f"Rate limited. Try again in {remaining}s"
                else:
                    del self._cooldowns[key]

            # Cleanup and check limit
            self._cleanup_old_calls(key, now)

            if len(self._calls[key]) >= self.config.max_calls:
                # Set cooldown
                self._cooldowns[key] = now + self.config.cooldown_seconds
                return (
                    False,
                    f"Too many requests. Limit: {self.config.max_calls}/{self.config.window_seconds}s",
                )

            # Record call
            self._calls[key].append(now)
            return True, "ok"

    def reset(self, user_id: int, tool_name: str | None = None):
        """Reset rate limit for user (admin function)."""
        with self._lock:
            if tool_name:
                key = f"{user_id}:{tool_name}"
                self._calls.pop(key, None)
                self._cooldowns.pop(key, None)
            else:
                # Reset all tools for user
                keys_to_remove = [k for k in self._calls if k.startswith(f"{user_id}:")]
                for k in keys_to_remove:
                    self._calls.pop(k, None)
                    self._cooldowns.pop(k, None)


# Global rate limiter instance
_rate_limiter = ToolRateLimiter()


def get_rate_limiter() -> ToolRateLimiter:
    return _rate_limiter
