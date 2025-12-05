from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    algorithm: str = "token_bucket"  # token_bucket, sliding_window, leaky_bucket
    capacity: int = 1000
    refill_rate: int = 100  # per second
    priority_enabled: bool = True


class TokenBucket:
    """
    Token Bucket Algorithm

    Features:
    - Allows bursts
    - Refills at constant rate
    - Capacity limit
    """

    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = threading.RLock()

    def allow(self, tokens: int = 1) -> bool:
        """Check if request is allowed"""
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = int(elapsed * self.refill_rate)

        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now


class SlidingWindowCounter:
    """
    Sliding Window Algorithm

    More accurate than fixed window
    Prevents boundary exploitation
    """

    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = threading.RLock()

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            return False


class LeakyBucket:
    """
    Leaky Bucket Algorithm

    Constant processing rate
    Queue with max size
    Smooth traffic flow
    """

    def __init__(self, capacity: int, leak_rate: int):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.queue: deque = deque(maxlen=capacity)
        self.last_leak = time.time()
        self._lock = threading.RLock()

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            self._leak()

            if len(self.queue) < self.capacity:
                self.queue.append(time.time())
                return True
            return False

    def _leak(self) -> None:
        """Process (leak) requests at constant rate"""
        now = time.time()
        elapsed = now - self.last_leak
        to_leak = int(elapsed * self.leak_rate)

        for _ in range(min(to_leak, len(self.queue))):
            self.queue.popleft()

        if to_leak > 0:
            self.last_leak = now
