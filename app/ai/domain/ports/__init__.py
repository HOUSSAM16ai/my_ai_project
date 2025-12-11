# app/ai/domain/ports/__init__.py
"""
Domain Ports (Interfaces) for LLM Client
=========================================
Protocols defining contracts for infrastructure adapters.

Following Hexagonal Architecture / Ports & Adapters pattern.
"""

from __future__ import annotations

from typing import Any, Generator, Protocol


# ======================================================================================
# LLM CLIENT PORT
# ======================================================================================


class LLMClientPort(Protocol):
    """
    Port for LLM client interactions.
    
    Infrastructure implementations:
    - OpenRouterTransport
    - OpenAITransport
    - AnthropicTransport
    - MockLLMTransport
    """

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a chat completion request.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response dictionary with 'content', 'usage', etc.
        """
        ...

    def chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Execute a streaming chat completion request.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            **kwargs: Additional parameters
            
        Yields:
            Response chunks with incremental content
        """
        ...


# ======================================================================================
# RETRY STRATEGY PORT
# ======================================================================================


class RetryStrategyPort(Protocol):
    """
    Port for retry logic.
    
    Implementations handle different retry patterns:
    - ExponentialBackoffRetry
    - LinearRetry
    - CustomRetry
    """

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        ...

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        ...

    @staticmethod
    def classify_error(error: Exception) -> str:
        """
        Classify error type for appropriate handling.
        
        Args:
            error: The exception to classify
            
        Returns:
            Error category (e.g., 'rate_limit', 'network', 'authentication')
        """
        ...


# ======================================================================================
# CIRCUIT BREAKER PORT
# ======================================================================================


class CircuitBreakerPort(Protocol):
    """
    Port for circuit breaker pattern.
    
    Implementations:
    - SimpleCircuitBreaker
    - SlidingWindowCircuitBreaker
    - AdaptiveCircuitBreaker
    """

    def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        ...

    def record_success(self) -> None:
        """Record successful operation"""
        ...

    def record_failure(self) -> None:
        """Record failed operation"""
        ...

    def is_open(self) -> bool:
        """Check if circuit is open"""
        ...

    def reset(self) -> None:
        """Reset circuit breaker state"""
        ...


# ======================================================================================
# COST MANAGER PORT
# ======================================================================================


class CostManagerPort(Protocol):
    """
    Port for cost tracking and management.
    
    Implementations:
    - BasicCostManager
    - TieredCostManager
    - BudgetAwareCostManager
    """

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Record token usage and calculate cost.
        
        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        ...

    def get_total_cost(self, model: str | None = None) -> float:
        """
        Get total accumulated cost.
        
        Args:
            model: Optional model filter
            
        Returns:
            Total cost in USD
        """
        ...

    def get_usage_stats(self) -> dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with usage stats (tokens, costs, etc.)
        """
        ...


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "LLMClientPort",
    "RetryStrategyPort",
    "CircuitBreakerPort",
    "CostManagerPort",
]
