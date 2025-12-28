"""
مدير التكلفة لتتبع استهلاك الرموز (Tokens).
Cost Manager for tracking token usage.
"""

import threading
from typing import Any

from app.core.logging import get_logger

_LOG = get_logger(__name__)


class CostManager:
    """
    يتتبع التكاليف المقدرة واستخدام الرموز.
    Tracks estimated costs and token usage.
    """

    _TOTAL_TOKENS: int = 0
    _TOTAL_COST: float = 0.0
    _LOCK: threading.Lock = threading.Lock()

    # Simplified pricing model (can be injected or config-based)
    # Price per 1k tokens
    from typing import ClassVar

    PRICING: ClassVar[dict[str, float]] = {
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.002,
        "default": 0.01
    }

    def update_metrics(
        self,
        model: str | None,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: float,
        finish_reason: str | None,
        error_kind: str | None = None
    ) -> None:
        """
        يحدث المقاييس بناءً على استخدام الطلب.
        Updates metrics based on request usage.
        """
        if not model or input_tokens is None or output_tokens is None:
            return

        total = input_tokens + output_tokens
        price_unit = self.PRICING.get(model, self.PRICING["default"])
        cost = (total / 1000.0) * price_unit

        with self._LOCK:
            self._TOTAL_TOKENS += total
            self._TOTAL_COST += cost

        # In a real system, we might push this to Prometheus/Datadog here.
        # _LOG.debug(f"Cost update: {total} tokens, ${cost:.4f}")

    def get_stats(self) -> dict[str, Any]:
        """
        يعيد الإحصائيات الحالية.
        Returns current statistics.
        """
        with self._LOCK:
            return {
                "total_tokens": self._TOTAL_TOKENS,
                "total_cost_usd": round(self._TOTAL_COST, 4)
            }
