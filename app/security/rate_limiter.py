# app/security/rate_limiter.py
import time
from collections import defaultdict
from enum import Enum

from fastapi import HTTPException, Request, status


class UserTier(Enum):
    """مستويات المستخدمين لتحديد المعدل"""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.history = defaultdict(list)

    async def __call__(self, request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()

        self.history[ip] = [t for t in self.history[ip] if now - t < 60]

        if len(self.history[ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
            )

        self.history[ip].append(now)


class AdaptiveRateLimiter:
    """
    محدد معدل متكيف يدعم مستويات المستخدمين المختلفة
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # Limits: (requests, window_seconds)
        self.limits = {
            UserTier.FREE: (60, 60),  # 60 req / 60 sec
            UserTier.PREMIUM: (1000, 60),  # 1000 req / 60 sec
            UserTier.ENTERPRISE: (10000, 60),  # 10000 req / 60 sec
        }
        # In-memory fallback
        self.memory_store = defaultdict(list)

    def check_rate_limit(
        self, request: Request, user_id: str | None = None, tier: UserTier = UserTier.FREE
    ) -> tuple[bool, dict]:
        """
        التحقق من حد المعدل للمستخدم أو عنوان IP

        Args:
            request: كائن الطلب
            user_id: معرف المستخدم (اختياري)
            tier: مستوى المستخدم

        Returns:
            (is_allowed, info_dict)
        """
        # Determine identification key (User ID preferred, else IP)
        key = str(user_id) if user_id else (request.client.host if request.client else "unknown")

        limit, window = self.limits.get(tier, self.limits[UserTier.FREE])
        now = time.time()

        # Clean up old entries
        self.memory_store[key] = [t for t in self.memory_store[key] if now - t < window]

        current_usage = len(self.memory_store[key])
        remaining = max(0, limit - current_usage)
        reset_time = (
            int(window - (now - self.memory_store[key][0]))
            if self.memory_store[key]
            else int(window)
        )

        if current_usage >= limit:
            return False, {"limit": limit, "remaining": 0, "reset_time": reset_time}

        self.memory_store[key].append(now)

        return True, {
            "limit": limit,
            "remaining": remaining - 1,  # -1 because we just added one
            "reset_time": reset_time,
        }


rate_limiter = RateLimiter(requests_per_minute=20)
