"""
Domain Models for LLM Client
=============================
Pure domain entities and value objects.

Following Domain-Driven Design (DDD) principles:
- Rich domain models with behavior
- Immutable value objects
- Clear boundaries and invariants
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENROUTER = 'openrouter'
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GOOGLE = 'google'
    MOCK = 'mock'


class MessageRole(str, Enum):
    """Chat message roles"""
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    FUNCTION = 'function'
    TOOL = 'tool'


class ErrorCategory(str, Enum):
    """Error classification categories"""
    RATE_LIMIT = 'rate_limit'
    AUTHENTICATION = 'authentication'
    INVALID_REQUEST = 'invalid_request'
    TIMEOUT = 'timeout'
    NETWORK = 'network'
    SERVER_ERROR = 'server_error'
    UNKNOWN = 'unknown'


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


@dataclass(frozen=True)
class Message:
    """
    Chat message value object.
    
    Immutable representation of a single message in a conversation.
    """
    role: MessageRole
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) ->dict[str, Any]:
        """Convert to API-compatible dictionary"""
        result: dict[str, Any] = {'role': self.role.value, 'content': self.
            content}
        if self.name:
            result['name'] = self.name
        if self.function_call:
            result['function_call'] = self.function_call
        if self.tool_calls:
            result['tool_calls'] = self.tool_calls
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) ->Message:
        """Create from dictionary"""
        return cls(role=MessageRole(data['role']), content=data.get(
            'content', ''), name=data.get('name'), function_call=data.get(
            'function_call'), tool_calls=data.get('tool_calls'))


@dataclass(frozen=True)
class TokenUsage:
    """
    Token usage value object.
    
    Tracks token consumption for billing and optimization.
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @property
    def cost(self) ->float:
        """Calculate approximate cost (placeholder - should use provider-specific pricing)"""
        return self.total_tokens / 1000 * 0.01


@dataclass(frozen=True)
class ModelResponse:
    """
    LLM response value object.
    
    Immutable representation of a complete LLM response.
    """
    content: str
    model: str
    usage: TokenUsage | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary"""
        return {'content': self.content, 'model': self.model, 'usage': {
            'prompt_tokens': self.usage.prompt_tokens, 'completion_tokens':
            self.usage.completion_tokens, 'total_tokens': self.usage.
            total_tokens} if self.usage else None, 'finish_reason': self.
            finish_reason, 'metadata': self.metadata, 'created_at': self.
            created_at.isoformat()}


@dataclass
class LLMRequest:
    """
    LLM request entity.
    
    Mutable entity representing a request in progress.
    Tracks state, attempts, and history.
    """
    id: str
    messages: list[Message]
    model: str
    provider: LLMProvider
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    attempts: int = 0
    last_error: Exception | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    extra_params: dict[str, Any] = field(default_factory=dict)

    def record_error(self, error: Exception) ->None:
        """Record the last error"""
        self.last_error = error
        self.updated_at = datetime.utcnow()


@dataclass
class CostRecord:
    """
    Cost tracking entity.
    
    Mutable entity for tracking cumulative costs.
    """
    model: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_tokens(self) ->int:
        """Total tokens consumed"""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def average_cost_per_request(self) ->float:
        """Average cost per request"""
        return (self.total_cost / self.request_count if self.request_count >
            0 else 0.0)


@dataclass
class CircuitBreakerStats:
    """
    Circuit breaker statistics entity.
    
    Tracks circuit breaker health and performance.
    """
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    total_calls: int = 0
    rejected_calls: int = 0

    def record_success(self) ->None:
        """Record successful operation"""
        self.success_count += 1
        self.total_calls += 1
        self.last_success_time = datetime.utcnow()

    def record_failure(self) ->None:
        """Record failed operation"""
        self.failure_count += 1
        self.total_calls += 1
        self.last_failure_time = datetime.utcnow()

    @property
    def success_rate(self) ->float:
        """Calculate success rate"""
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls

    @property
    def failure_rate(self) ->float:
        """Calculate failure rate"""
        if self.total_calls == 0:
            return 0.0
        return self.failure_count / self.total_calls


__all__ = ['LLMProvider', 'MessageRole', 'ErrorCategory', 'CircuitState',
    'Message', 'TokenUsage', 'ModelResponse', 'LLMRequest', 'CostRecord',
    'CircuitBreakerStats']
