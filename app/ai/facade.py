# app/ai/facade.py
"""
LLM Client Service - Backward Compatible Facade
================================================
Thin facade maintaining backward compatibility with original API.

This file delegates to the refactored layered architecture:
- Domain ports in domain/ports/
- Application services in application/
- Infrastructure transports in infrastructure/transports/

Original file: llm_client_service.py (complex monolith)
Refactored: Clean delegation to specialized components

Architecture:
- PayloadBuilder: Request construction
- ResponseNormalizer: Response processing
- CircuitBreaker: Failure protection
- CostManager: Budget tracking
- RetryStrategy: Intelligent retries
- Transports: Provider-specific implementations
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Callable, Generator

from app.ai.application.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    get_circuit_breaker,
)
from app.ai.application.cost_manager import (
    BudgetConfig,
    BudgetPeriod,
    CostManager,
    get_cost_manager,
)
from app.ai.application.payload_builder import PayloadBuilder
from app.ai.application.response_normalizer import ResponseNormalizer
from app.ai.application.retry_strategy import (
    AdaptiveRetry,
    ExponentialBackoffRetry,
    RetryConfig,
    RetryExecutor,
)
from app.ai.infrastructure.transports import (
    MockLLMTransport,
    OpenRouterTransport,
    get_transport,
)

_LOG = logging.getLogger(__name__)


class LLMClientService:
    """
    Facade for LLM Client operations.
    
    **REFACTORED**: This class now delegates to specialized services
    instead of implementing everything inline.
    
    Maintains 100% backward compatibility with original API while
    using clean layered architecture internally.
    
    Original responsibilities now delegated to:
    - PayloadBuilder: Request construction
    - ResponseNormalizer: Response processing
    - CircuitBreaker: Failure protection
    - CostManager: Budget and cost tracking
    - RetryStrategy: Intelligent retry logic
    - Transports: Provider-specific implementations
    """
    
    def __init__(
        self,
        provider: str | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        retry_config: RetryConfig | None = None,
    ):
        """
        Initialize LLM Client Service.
        
        Args:
            provider: LLM provider (openrouter, openai, anthropic, mock)
            circuit_breaker_config: Circuit breaker configuration
            retry_config: Retry strategy configuration
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openrouter")
        
        self.payload_builder = PayloadBuilder()
        self.cost_manager = get_cost_manager()
        self.response_normalizer = ResponseNormalizer(cost_manager=self.cost_manager)
        
        self.circuit_breaker = get_circuit_breaker(
            f"llm_client_{self.provider}",
            circuit_breaker_config
        )
        
        retry_strategy = AdaptiveRetry(retry_config) if retry_config else AdaptiveRetry()
        self.retry_executor = RetryExecutor(retry_strategy)
        
        self._transport = None
        self._transport_lock = threading.RLock()
        
        self._pre_hooks: list[Callable[[dict[str, Any]], None]] = []
        self._post_hooks: list[Callable[[dict[str, Any], dict[str, Any]], None]] = []
        
        self._initialize_default_budgets()
    
    def _initialize_default_budgets(self) -> None:
        """Initialize default budget configurations."""
        daily_limit = float(os.getenv("LLM_DAILY_BUDGET", "100.0"))
        monthly_limit = float(os.getenv("LLM_MONTHLY_BUDGET", "3000.0"))
        
        self.cost_manager.set_budget(
            "global_daily",
            BudgetConfig(
                limit=daily_limit,
                period=BudgetPeriod.DAILY,
                soft_limit_percentage=0.8,
                hard_limit_percentage=1.0,
                auto_reset=True,
            )
        )
        
        self.cost_manager.set_budget(
            "global_monthly",
            BudgetConfig(
                limit=monthly_limit,
                period=BudgetPeriod.MONTHLY,
                soft_limit_percentage=0.9,
                hard_limit_percentage=1.0,
                auto_reset=True,
            )
        )
    
    def _get_transport(self) -> Any:
        """Get or create transport instance."""
        if self._transport is not None:
            return self._transport
        
        with self._transport_lock:
            if self._transport is None:
                self._transport = get_transport(self.provider)
                _LOG.info(f"Initialized transport: {self.provider}")
            return self._transport
    
    def invoke_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        user_id: str | None = None,
        project_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any] | Generator[dict[str, Any], None, None]:
        """
        Invoke LLM chat completion.
        
        Args:
            model: Model identifier
            messages: List of message dictionaries
            tools: Optional tool definitions
            tool_choice: Tool selection strategy
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Enable streaming response
            user_id: Optional user identifier for cost tracking
            project_id: Optional project identifier for cost tracking
            extra: Additional parameters
            
        Returns:
            Response dictionary or generator for streaming
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            BudgetExceededError: If budget limit exceeded
            Exception: Various LLM provider errors
        """
        if not self.circuit_breaker.is_available():
            raise RuntimeError(
                f"Circuit breaker is OPEN for {self.provider}. "
                f"Service temporarily unavailable."
            )
        
        payload = self.payload_builder.build(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            extra=extra,
        )
        
        for hook in self._pre_hooks:
            try:
                hook(payload)
            except Exception as e:
                _LOG.warning(f"Pre-hook error: {e}")
        
        if stream:
            return self._invoke_streaming(payload, user_id, project_id)
        else:
            return self._invoke_non_streaming(payload, user_id, project_id)
    
    def _invoke_non_streaming(
        self,
        payload: dict[str, Any],
        user_id: str | None,
        project_id: str | None,
    ) -> dict[str, Any]:
        """Execute non-streaming request with retry and circuit breaker."""
        start_time = time.time()
        retry_schedule: list[float] = []
        
        def _execute() -> dict[str, Any]:
            transport = self._get_transport()
            
            t0 = time.perf_counter()
            completion = transport.chat_completion(
                messages=payload["messages"],
                model=payload["model"],
                tools=payload.get("tools"),
                tool_choice=payload.get("tool_choice"),
                temperature=payload.get("temperature", 0.7),
                max_tokens=payload.get("max_tokens"),
            )
            latency_ms = (time.perf_counter() - t0) * 1000.0
            
            envelope = self.response_normalizer.normalize(
                completion=completion,
                payload=payload,
                latency_ms=latency_ms,
                start_ts=start_time,
                end_ts=time.time(),
                retry_schedule=retry_schedule,
                attempts=1,
            )
            
            if "usage" in envelope:
                usage = envelope["usage"]
                self.cost_manager.track_usage(
                    model=payload["model"],
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    user_id=user_id,
                    project_id=project_id,
                    request_id=envelope.get("request_id"),
                )
            
            for hook in self._post_hooks:
                try:
                    hook(payload, envelope)
                except Exception as e:
                    _LOG.warning(f"Post-hook error: {e}")
            
            return envelope
        
        try:
            result = self.circuit_breaker.call(
                lambda: self.retry_executor.execute(_execute)
            )
            return result
        except Exception as e:
            _LOG.error(f"LLM invocation failed: {e}")
            raise
    
    def _invoke_streaming(
        self,
        payload: dict[str, Any],
        user_id: str | None,
        project_id: str | None,
    ) -> Generator[dict[str, Any], None, None]:
        """Execute streaming request."""
        transport = self._get_transport()
        
        try:
            stream = transport.chat_completion_stream(
                messages=payload["messages"],
                model=payload["model"],
                tools=payload.get("tools"),
                tool_choice=payload.get("tool_choice"),
                temperature=payload.get("temperature", 0.7),
                max_tokens=payload.get("max_tokens"),
            )
            
            accumulated_tokens = 0
            for chunk in stream:
                if "content" in chunk:
                    accumulated_tokens += len(chunk["content"].split())
                yield chunk
            
            if accumulated_tokens > 0:
                self.cost_manager.track_usage(
                    model=payload["model"],
                    input_tokens=len(str(payload["messages"]).split()),
                    output_tokens=accumulated_tokens,
                    user_id=user_id,
                    project_id=project_id,
                )
        
        except Exception as e:
            _LOG.error(f"Streaming invocation failed: {e}")
            raise
    
    def register_pre_hook(self, hook: Callable[[dict[str, Any]], None]) -> None:
        """Register pre-invocation hook."""
        self._pre_hooks.append(hook)
    
    def register_post_hook(
        self,
        hook: Callable[[dict[str, Any], dict[str, Any]], None]
    ) -> None:
        """Register post-invocation hook."""
        self._post_hooks.append(hook)
    
    def get_cost_metrics(self) -> dict[str, Any]:
        """Get cost metrics."""
        metrics = self.cost_manager.get_metrics()
        return {
            "total_cost": metrics.total_cost,
            "total_requests": metrics.total_requests,
            "total_input_tokens": metrics.total_input_tokens,
            "total_output_tokens": metrics.total_output_tokens,
            "cost_by_model": metrics.cost_by_model,
            "average_cost_per_request": metrics.average_cost_per_request,
        }
    
    def get_budget_status(self, budget_id: str = "global_daily") -> dict[str, Any]:
        """Get budget status."""
        return self.cost_manager.get_budget_status(budget_id)
    
    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """Get circuit breaker status."""
        metrics = self.circuit_breaker.get_metrics()
        return {
            "state": self.circuit_breaker.get_state().value,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "rejected_requests": metrics.rejected_requests,
            "failure_rate": metrics.failure_rate,
            "is_available": self.circuit_breaker.is_available(),
        }
    
    def get_retry_metrics(self) -> dict[str, Any]:
        """Get retry metrics."""
        metrics = self.retry_executor.strategy.get_metrics()
        return {
            "total_attempts": metrics.total_attempts,
            "successful_retries": metrics.successful_retries,
            "failed_retries": metrics.failed_retries,
            "total_delay": metrics.total_delay,
            "average_attempts": metrics.average_attempts,
            "retries_by_category": {
                k.value: v for k, v in metrics.retries_by_category.items()
            },
        }
    
    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker."""
        self.circuit_breaker.reset()
        _LOG.info("Circuit breaker reset")
    
    def set_user_budget(
        self,
        user_id: str,
        daily_limit: float,
        monthly_limit: float | None = None
    ) -> None:
        """Set budget limits for specific user."""
        self.cost_manager.set_budget(
            f"user:{user_id}",
            BudgetConfig(
                limit=daily_limit,
                period=BudgetPeriod.DAILY,
                auto_reset=True,
            )
        )
        
        if monthly_limit:
            self.cost_manager.set_budget(
                f"user:{user_id}_monthly",
                BudgetConfig(
                    limit=monthly_limit,
                    period=BudgetPeriod.MONTHLY,
                    auto_reset=True,
                )
            )
    
    def set_project_budget(
        self,
        project_id: str,
        daily_limit: float,
        monthly_limit: float | None = None
    ) -> None:
        """Set budget limits for specific project."""
        self.cost_manager.set_budget(
            f"project:{project_id}",
            BudgetConfig(
                limit=daily_limit,
                period=BudgetPeriod.DAILY,
                auto_reset=True,
            )
        )
        
        if monthly_limit:
            self.cost_manager.set_budget(
                f"project:{project_id}_monthly",
                BudgetConfig(
                    limit=monthly_limit,
                    period=BudgetPeriod.MONTHLY,
                    auto_reset=True,
                )
            )


# ======================================================================================
# GLOBAL SINGLETON (for backward compatibility)
# ======================================================================================

_GLOBAL_CLIENT: LLMClientService | None = None
_GLOBAL_LOCK = threading.RLock()


def get_llm_client_service(provider: str | None = None) -> LLMClientService:
    """
    Get global LLM client service instance.
    
    Args:
        provider: Optional provider override
        
    Returns:
        LLMClientService instance
    """
    global _GLOBAL_CLIENT
    
    if _GLOBAL_CLIENT is not None and (provider is None or provider == _GLOBAL_CLIENT.provider):
        return _GLOBAL_CLIENT
    
    with _GLOBAL_LOCK:
        if _GLOBAL_CLIENT is None or (provider and provider != _GLOBAL_CLIENT.provider):
            _GLOBAL_CLIENT = LLMClientService(provider)
            _LOG.info(f"Initialized global LLM client service: {_GLOBAL_CLIENT.provider}")
        return _GLOBAL_CLIENT


def reset_llm_client_service() -> None:
    """Reset global LLM client service."""
    global _GLOBAL_CLIENT
    with _GLOBAL_LOCK:
        _GLOBAL_CLIENT = None
        _LOG.info("Global LLM client service reset")


# ======================================================================================
# CONVENIENCE FUNCTIONS (backward compatibility)
# ======================================================================================


def invoke_chat(
    model: str,
    messages: list[dict[str, str]],
    **kwargs: Any
) -> dict[str, Any] | Generator[dict[str, Any], None, None]:
    """Convenience function for chat invocation."""
    client = get_llm_client_service()
    return client.invoke_chat(model, messages, **kwargs)


def get_cost_metrics() -> dict[str, Any]:
    """Convenience function for cost metrics."""
    client = get_llm_client_service()
    return client.get_cost_metrics()


def get_circuit_breaker_status() -> dict[str, Any]:
    """Convenience function for circuit breaker status."""
    client = get_llm_client_service()
    return client.get_circuit_breaker_status()
