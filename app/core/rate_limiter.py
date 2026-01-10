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

    # Maximum number of unique user:tool keys to track (prevents unbounded growth)
    _MAX_KEYS = 10000

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._cooldowns: dict[str, float] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_old_calls(self, key: str, now: float):
        """Remove calls outside the time window."""
        cutoff = now - self.config.window_seconds
        self._calls[key] = [t for t in self._calls[key] if t > cutoff]

    def _cleanup_expired_keys(self, now: float) -> None:
        """Remove keys with no recent calls."""
        cutoff = now - self.config.window_seconds
        keys_to_remove = []
        for key, calls in list(self._calls.items()):
            fresh_calls = [t for t in calls if t > cutoff]
            if not fresh_calls:
                keys_to_remove.append(key)
            else:
                self._calls[key] = fresh_calls

        for key in keys_to_remove:
            self._calls.pop(key, None)

    def _cleanup_expired_cooldowns(self, now: float) -> None:
        """Remove expired cooldowns."""
        for key in list(self._cooldowns.keys()):
            if self._cooldowns[key] < now:
                self._cooldowns.pop(key, None)

    def _enforce_max_keys_limit(self) -> None:
        """Ensure the number of keys does not exceed the maximum allowed."""
        if len(self._calls) <= self._MAX_KEYS:
            return

        # Sort by most recent call and keep only the newest
        sorted_keys = sorted(
            self._calls.keys(),
            key=lambda k: max(self._calls[k]) if self._calls[k] else 0,
        )
        keys_to_remove = sorted_keys[: len(sorted_keys) - self._MAX_KEYS]
        for key in keys_to_remove:
            self._calls.pop(key, None)

    def _periodic_cleanup(self, now: float) -> None:
        """Periodic cleanup to prevent memory leaks from abandoned keys."""
        # Only run cleanup every 5 minutes
        if now - self._last_cleanup < 300:
            return

        self._last_cleanup = now
        self._cleanup_expired_keys(now)
        self._cleanup_expired_cooldowns(now)
        self._enforce_max_keys_limit()

    def _is_cooling_down(self, key: str, now: float) -> tuple[bool, str]:
        """Check if the key is currently in cooldown."""
        if key in self._cooldowns:
            cooldown_end = self._cooldowns[key]
            if now < cooldown_end:
                remaining = int(cooldown_end - now)
                return True, f"Rate limited. Try again in {remaining}s"
            del self._cooldowns[key]
        return False, ""

    def _check_rate_limit(self, key: str, now: float) -> tuple[bool, str]:
        """Check if the call limit has been reached."""
        self._cleanup_old_calls(key, now)

        if len(self._calls[key]) >= self.config.max_calls:
            self._cooldowns[key] = now + self.config.cooldown_seconds
            return (
                False,
                f"Too many requests. Limit: {self.config.max_calls}/{self.config.window_seconds}s",
            )
        return True, "ok"

    def check(self, user_id: int, tool_name: str) -> tuple[bool, str]:
        """
        Check if a tool call is allowed.

        Returns:
            (allowed: bool, reason: str)
        """
        key = f"{user_id}:{tool_name}"
        now = time.time()

        with self._lock:
            # Run periodic cleanup to prevent memory leaks
            self._periodic_cleanup(now)

            is_cooling, reason = self._is_cooling_down(key, now)
            if is_cooling:
                return False, reason

            allowed, reason = self._check_rate_limit(key, now)
            if not allowed:
                return False, reason

            # Record call
            self._calls[key].append(now)
            return True, "ok"

    def reset(self, user_id: int, tool_name: str | None = None) -> None:
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
