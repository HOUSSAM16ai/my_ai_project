"""
نظام التوجيه الذكي (Intelligent Routing System).

يحتوي هذا الملف على المنطق الأساسي لتوجيه الطلبات بين مزودي الخدمة المختلفين،
مع مراعاة التكلفة، وزمن الاستجابة، وصحة الخدمة (Circuit Breaker).

المبادئ (Principles):
- Resilience: استخدام قاطع الدائرة لمنع الفشل المتسلسل.
- Intelligence: اتخاذ قرارات التوجيه بناءً على البيانات.
- KISS: تقسيم المنطق المعقد إلى دوال صغيرة ومفهومة.
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any

from .models import LoadBalancerState, ProtocolType, RoutingDecision, RoutingStrategy
from .providers.anthropic import AnthropicAdapter
from .providers.base import ModelProviderAdapter
from .providers.openai import OpenAIAdapter
from .strategies.implementations import get_strategy

logger = logging.getLogger(__name__)


class SuperCircuitBreaker:
    """
    قاطع الدائرة الخارق (Super Circuit Breaker).

    يمنع الفشل المتسلسل عبر إيقاف إرسال الطلبات إلى الخدمات المتعثرة مؤقتاً.
    يدعم حالات: Closed (يعمل)، Open (متوقف)، Half-Open (اختبار التعافي).
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state: dict[str, dict[str, Any]] = {}
        self.lock = threading.RLock()

    def report_failure(self, service_id: str) -> None:
        """تسجيل فشل لخدمة معينة وتحديث حالتها."""
        with self.lock:
            if service_id not in self.state:
                self._init_service_state(service_id)

            self.state[service_id]["failures"] += 1
            self.state[service_id]["last_failure"] = datetime.now(UTC)

            if self.state[service_id]["failures"] >= self.failure_threshold:
                self.state[service_id]["open"] = True
                logger.warning(
                    f"Circuit Breaker OPEN for {service_id}. Failures: {self.state[service_id]['failures']}"
                )

    def report_success(self, service_id: str) -> None:
        """تسجيل نجاح وإعادة تعيين عداد الفشل."""
        with self.lock:
            if service_id in self.state:
                self.state[service_id]["failures"] = 0
                self.state[service_id]["open"] = False

    def is_open(self, service_id: str) -> bool:
        """التحقق مما إذا كانت الدائرة مفتوحة (الخدمة محظورة)."""
        with self.lock:
            if service_id not in self.state:
                return False
            if not self.state[service_id]["open"]:
                return False

            return not self._should_attempt_recovery(service_id)

    def _init_service_state(self, service_id: str) -> None:
        self.state[service_id] = {
            "failures": 0,
            "last_failure": None,
            "open": False,
        }

    def _should_attempt_recovery(self, service_id: str) -> bool:
        last_failure = self.state[service_id].get("last_failure")
        if last_failure:
            elapsed = (datetime.now(UTC) - last_failure).total_seconds()
            if elapsed > self.recovery_timeout:
                logger.info(f"Circuit Breaker HALF-OPEN for {service_id}")
                return True
        return False


class IntelligentRouter:
    """
    محرك التوجيه الذكي (Intelligent Routing Engine).

    المميزات:
    - توجيه مدرك للتكلفة (Cost-aware).
    - توجيه محسن لزمن الاستجابة (Latency-optimized).
    - موازنة الأحمال بين المزودين.
    - تكامل مع قاطع الدائرة.
    """

    def __init__(self) -> None:
        self.provider_adapters: dict[str, ModelProviderAdapter] = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
        }
        self.routing_history: deque[dict[str, Any]] = deque(maxlen=10000)
        self.circuit_breaker = SuperCircuitBreaker()

        # تهيئة ديناميكية لحالة موازن الأحمال
        class AutoInitDict(dict[str, LoadBalancerState]):
            def __missing__(self, key: str) -> LoadBalancerState:
                value = LoadBalancerState(service_id=str(key))
                self[key] = value
                return value

        self.provider_stats: dict[str, LoadBalancerState] = AutoInitDict()
        self.lock = threading.RLock()

    def route_request(
        self,
        model_type: str,
        estimated_tokens: int,
        strategy: RoutingStrategy = RoutingStrategy.INTELLIGENT,
        constraints: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """
        توجيه الطلب إلى أنسب مزود خدمة.

        Args:
            model_type: نوع النموذج المطلوب.
            estimated_tokens: عدد الرموز المقدرة.
            strategy: استراتيجية التوجيه.
            constraints: قيود إضافية (التكلفة القصوى، الخ).
        """
        constraints = constraints or {}
        candidates = self._evaluate_candidates(model_type, estimated_tokens, constraints)

        if not candidates:
            raise ValueError("No suitable provider found for routing (or all circuits open)")

        best_candidate = self._apply_strategy_and_select_best(candidates, strategy)
        decision = self._create_routing_decision(best_candidate, strategy, len(candidates))
        self._record_decision(decision, model_type, estimated_tokens)

        return decision

    def _evaluate_candidates(
        self, model_type: str, estimated_tokens: int, constraints: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """تقييم وترشيح المزودين المتاحين بناءً على القيود."""
        max_cost = constraints.get("max_cost", float("inf"))
        max_latency = constraints.get("max_latency", float("inf"))
        candidates: list[dict[str, Any]] = []

        for provider_name, adapter in self.provider_adapters.items():
            if self._is_provider_available(provider_name):
                candidate = self._evaluate_single_provider(
                    provider_name, adapter, model_type, estimated_tokens, max_cost, max_latency
                )
                if candidate:
                    candidates.append(candidate)

        return candidates

    def _is_provider_available(self, provider_name: str) -> bool:
        if self.circuit_breaker.is_open(provider_name):
            logger.warning(f"Skipping {provider_name} due to open circuit.")
            return False
        return True

    def _evaluate_single_provider(
        self,
        provider_name: str,
        adapter: ModelProviderAdapter,
        model_type: str,
        tokens: int,
        max_cost: float,
        max_latency: float,
    ) -> dict[str, Any] | None:
        try:
            cost = adapter.estimate_cost(model_type, tokens)
            latency = adapter.estimate_latency(model_type, tokens)

            if cost > max_cost or latency > max_latency:
                return None

            with self.lock:
                stats = self.provider_stats[provider_name]
            health_score = 1.0 if stats.is_healthy else 0.0

            return {
                "provider": provider_name,
                "cost": cost,
                "latency": latency,
                "health_score": health_score,
            }
        except Exception as e:
            logger.warning(f"Error evaluating provider {provider_name}: {e}")
            return None

    def _apply_strategy_and_select_best(
        self, candidates: list[dict[str, Any]], strategy: RoutingStrategy
    ) -> dict[str, Any]:
        """تطبيق استراتيجية التوجيه واختيار الأفضل."""
        strategy_impl = get_strategy(strategy)
        strategy_impl.calculate_scores(candidates)
        return max(candidates, key=lambda x: x["score"])

    def _create_routing_decision(
        self,
        best_candidate: dict[str, Any],
        strategy: RoutingStrategy,
        candidate_count: int,
    ) -> RoutingDecision:
        """إنشاء كائن قرار التوجيه النهائي."""
        return RoutingDecision(
            service_id=str(best_candidate["provider"]),
            base_url=f"https://api.{best_candidate['provider']}.com",
            protocol=ProtocolType.REST,
            estimated_latency_ms=float(best_candidate["latency"]),
            estimated_cost=float(best_candidate["cost"]),
            confidence_score=float(best_candidate["score"]),
            reasoning=f"Selected {best_candidate['provider']} based on {strategy.value} strategy",
            metadata={"all_candidates": candidate_count},
        )

    def _record_decision(
        self,
        decision: RoutingDecision,
        model_type: str,
        estimated_tokens: int,
    ) -> None:
        """تسجيل القرار في الأرشيف."""
        with self.lock:
            self.routing_history.append(
                {
                    "timestamp": datetime.now(UTC),
                    "decision": decision,
                    "model_type": model_type,
                    "tokens": estimated_tokens,
                }
            )

    def update_provider_stats(self, provider: str, success: bool, latency_ms: float) -> None:
        """تحديث إحصائيات المزود بعد تنفيذ الطلب."""
        if success:
            self.circuit_breaker.report_success(provider)
        else:
            self.circuit_breaker.report_failure(provider)

        with self.lock:
            stats = self.provider_stats[provider]
            self._update_load_balancer_stats(stats, success, latency_ms)

    def _update_load_balancer_stats(
        self, stats: LoadBalancerState, success: bool, latency_ms: float
    ) -> None:
        stats.total_requests += 1
        if not success:
            stats.total_errors += 1

        stats.avg_latency_ms = (
            stats.avg_latency_ms * (stats.total_requests - 1) + latency_ms
        ) / stats.total_requests

        error_rate = (
            stats.total_errors / stats.total_requests if stats.total_requests > 0 else 0
        )
        stats.is_healthy = error_rate < 0.1
