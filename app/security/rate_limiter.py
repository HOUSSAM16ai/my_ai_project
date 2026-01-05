# app/security/rate_limiter.py
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, status


class UserTier(Enum):
    """مستويات المستخدمين لتحديد المعدل."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass(slots=True)
class RateLimitStatus:
    """حالة محدد المعدل مع بيانات دقيقة للحدود المتبقية."""

    limit: int
    remaining: int
    reset_time: int


class RateLimiter:
    """محدد معدل بسيط يعتمد على عنوان الـ IP فقط."""

    def __init__(self, requests_per_minute: int) -> None:
        """تهيئة المحدد بعدد الطلبات المسموح بها في الدقيقة."""

        self.requests_per_minute = requests_per_minute
        self.history: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        """التحقق من الحد قبل تمرير الطلب إلى المسار التالي."""

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        self.history[ip] = [timestamp for timestamp in self.history[ip] if now - timestamp < 60]

        if len(self.history[ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
            )

        self.history[ip].append(now)


class AdaptiveRateLimiter:
    """محدد معدل متكيف يدعم مستويات المستخدمين المختلفة مع مخزن احتياطي في الذاكرة."""

    def __init__(self, redis_client: object | None = None) -> None:
        """تهيئة المحدد مع حدود افتراضية ومخزن احتياطي."""

        self.redis_client = redis_client
        self.limits: dict[UserTier, tuple[int, int]] = {
            UserTier.FREE: (60, 60),  # 60 req / 60 sec
            UserTier.PREMIUM: (1000, 60),  # 1000 req / 60 sec
            UserTier.ENTERPRISE: (10000, 60),  # 10000 req / 60 sec
        }
        self.memory_store: dict[str, list[float]] = defaultdict(list)

    def _resolve_key(self, request: Request, user_id: str | None) -> str:
        """تحديد مفتاح التتبع بناءً على معرف المستخدم أو عنوان الـ IP."""

        if user_id:
            return str(user_id)
        return request.client.host if request.client else "unknown"

    def _get_limit_window(self, tier: UserTier) -> tuple[int, int]:
        """استرجاع الحد والنافذة الزمنية المناسبة للمستوى المطلوب."""

        return self.limits.get(tier, self.limits[UserTier.FREE])

    def _prune_window(self, key: str, window: int, now: float) -> None:
        """تنظيف السجلات القديمة خارج النافذة الزمنية للحفاظ على الدقة."""

        self.memory_store[key] = [timestamp for timestamp in self.memory_store[key] if now - timestamp < window]

    def _calculate_reset_time(self, key: str, window: int, now: float) -> int:
        """حساب الزمن المتبقي لإعادة الضبط بناءً على أقدم طلب مسجل."""

        if not self.memory_store[key]:
            return int(window)

        return int(window - (now - self.memory_store[key][0]))

    def _record_request(self, key: str, now: float) -> None:
        """تسجيل طلب جديد في الذاكرة الاحتياطية بعد تجاوز الفحوصات."""

        self.memory_store[key].append(now)

    def check_rate_limit(
        self, request: Request, user_id: str | None = None, tier: UserTier = UserTier.FREE
    ) -> tuple[bool, RateLimitStatus]:
        """
        التحقق من حد المعدل للمستخدم أو عنوان IP مع إرجاع بيانات مفصلة.

        Args:
            request: كائن الطلب الحالي.
            user_id: معرف المستخدم إن توفر لتفضيل التتبع على عنوان الـ IP.
            tier: مستوى المستخدم الذي يحدد حدود الاستهلاك.

        Returns:
            tuple[bool, RateLimitStatus]: سماح الطلب وحالته الحالية.
        """

        key = self._resolve_key(request, user_id)
        limit, window = self._get_limit_window(tier)
        now = time.time()

        self._prune_window(key, window, now)
        current_usage = len(self.memory_store[key])
        reset_time = self._calculate_reset_time(key, window, now)

        if current_usage >= limit:
            return False, RateLimitStatus(limit=limit, remaining=0, reset_time=reset_time)

        self._record_request(key, now)
        remaining = max(0, limit - len(self.memory_store[key]))

        return True, RateLimitStatus(limit=limit, remaining=remaining, reset_time=reset_time)


rate_limiter = RateLimiter(requests_per_minute=20)
