import contextlib
import logging
import os
import random
import time
from collections.abc import Generator
from typing import Any
from app.core.ai_client_factory import get_ai_client
from app.services.llm.circuit_breaker import CircuitBreaker
from app.services.llm.cost_manager import CostManager
from app.services.llm.retry_strategy import RetryStrategy
_LOG = logging.getLogger(__name__)


class LLMSettings:
    """Encapsulates LLM invocation settings."""

    def __init__(self):
        self.extreme_mode = os.getenv('LLM_EXTREME_COMPLEXITY_MODE', '0'
            ) == '1'
        self.ultimate_mode = os.getenv('LLM_ULTIMATE_COMPLEXITY_MODE', '0'
            ) == '1'
        default_retries = ('20' if self.ultimate_mode else '8' if self.
            extreme_mode else '2')
        self.max_retries = int(os.getenv('LLM_MAX_RETRIES', default_retries))
        default_backoff = ('1.8' if self.ultimate_mode else '1.5' if self.
            extreme_mode else '1.3')
        self.retry_backoff_base = float(os.getenv('LLM_RETRY_BACKOFF_BASE',
            default_backoff))
        self.retry_jitter = os.getenv('LLM_RETRY_JITTER', '1') == '1'
        self.enable_stream = os.getenv('LLM_ENABLE_STREAM', '0') == '1'
        self.log_attempts = os.getenv('LLM_LOG_ATTEMPTS', '1') == '1'
        self.sanitize_output = os.getenv('LLM_SANITIZE_OUTPUT', '0') == '1'
        self.force_model = os.getenv('LLM_FORCE_MODEL', '').strip() or None


class LLMPayload:
    """Encapsulates the LLM request payload."""

    def __init__(self, model: str, messages: list[dict[str, str]], tools: (
        list[dict[str, Any]] | None), tool_choice: (str | None),
        temperature: float, max_tokens: (int | None), extra: (dict[str, Any
        ] | None), force_model: (str | None)=None):
        self.model = force_model if force_model else model
        self.messages = messages
        self.tools = tools
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra = extra or {}

    def to_dict(self) ->dict[str, Any]:
        return {'model': self.model, 'messages': self.messages, 'tools':
            self.tools, 'tool_choice': self.tool_choice, 'temperature':
            self.temperature, 'max_tokens': self.max_tokens, 'extra': self.
            extra}


class ResponseSanitizer:
    """Handles sanitization of LLM responses."""
    _SENSITIVE_MARKERS = 'OPENAI_API_KEY=', 'sk-or-', 'sk-'

    @classmethod
    def sanitize(cls, text: str, enabled: bool=True) ->str:
        if not enabled or not isinstance(text, str):
            return text
        sanitized = text.replace('\r', '')
        for marker in cls._SENSITIVE_MARKERS:
            if marker in sanitized:
                sanitized = sanitized.replace(marker, f'[REDACTED:{marker}]')
        try:
            import json
            regexes = json.loads(os.getenv('LLM_SANITIZE_REGEXES_JSON', '[]'))
        except Exception:
            regexes = []
        import re
        for pattern in regexes:
            with contextlib.suppress(Exception):
                sanitized = re.sub(pattern, '[REDACTED_PATTERN]', sanitized)
        return sanitized


class LLMRequestExecutor:
    """
    Handles the execution of a single LLM request, including retries,
    circuit breaking, and metrics.
    """

    def __init__(self):
        self.settings = LLMSettings()
        self.breaker = CircuitBreaker()
        self.cost_manager = CostManager()
        self.client = get_ai_client()
        self.retry_schedule: list[float] = []

    def execute(self, payload: LLMPayload) ->dict[str, Any]:
        if not self.breaker.is_allowed:
            raise RuntimeError(
                'LLM circuit breaker OPEN – rejecting invocation temporarily.')
        start_time = time.time()
        attempts = 0
        backoff = self.settings.retry_backoff_base
        last_exc: Exception | None = None
        while attempts <= self.settings.max_retries:
            attempts += 1
            t0 = time.perf_counter()
            try:
                response = self._make_api_call(payload)
                latency_ms = (time.perf_counter() - t0) * 1000.0
                return self._process_success(response, payload, attempts,
                    start_time, latency_ms)
            except Exception as exc:
                last_exc = exc
                self._handle_error(exc, payload.model, attempts, backoff)
                sleep_for = backoff
                if self.settings.retry_jitter:
                    sleep_for += random.random() * 0.25
                self.retry_schedule.append(round(sleep_for, 3))
                time.sleep(sleep_for)
                backoff *= self.settings.retry_backoff_base
        raise RuntimeError(
            f'LLM invocation failed after {attempts} attempts. Last error: {last_exc}'
            )

    def _make_api_call(self, payload: LLMPayload):
        return self.client.chat.completions.create(model=payload.model,
            messages=payload.messages, tools=payload.tools, tool_choice=
            payload.tool_choice, temperature=payload.temperature,
            max_tokens=payload.max_tokens)

    def _process_success(self, completion: Any, payload: LLMPayload,
        attempts: int, start_time: float, latency_ms: float) ->dict[str, Any]:
        content = getattr(completion.choices[0].message, 'content', '')
        tool_calls = getattr(completion.choices[0].message, 'tool_calls', None)
        usage = self._extract_usage(completion)
        if (content is None or isinstance(content, str) and content.strip() ==
            '') and not tool_calls:
            _LOG.warning(
                f'Empty response from {payload.model} at attempt {attempts}')
            raise RuntimeError(
                f'Empty response (no content/tools). Attempt {attempts}')
        content = ResponseSanitizer.sanitize(content, self.settings.
            sanitize_output)
        pt, ct, total = usage['prompt_tokens'], usage['completion_tokens'
            ], usage['total_tokens']
        cost = self.cost_manager.estimate_cost(payload.model, pt, ct)
        self.cost_manager.update_metrics(pt, ct, total, latency_ms, cost)
        return {'content': content, 'tool_calls': tool_calls, 'usage':
            usage, 'model': payload.model, 'latency_ms': round(latency_ms, 
            2), 'cost': cost, 'raw': completion, 'meta': {'attempts':
            attempts, 'forced_model': False, 'stream': False, 'start_ts':
            start_time, 'end_ts': time.time(), 'retry_schedule': self.
            retry_schedule}}

    def _extract_usage(self, completion: Any) ->dict[str, int]:
        usage = getattr(completion, 'usage', {}) or {}
        if hasattr(usage, 'prompt_tokens'):
            return {'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens,
                'total_tokens': usage.total_tokens}
        usage_dict = usage if isinstance(usage, dict) else {}
        return {'prompt_tokens': usage_dict.get('prompt_tokens', 0),
            'completion_tokens': usage_dict.get('completion_tokens', 0),
            'total_tokens': usage_dict.get('total_tokens', 0)}

    def _handle_error(self, exc: Exception, model: str, attempts: int,
        backoff: float):
        kind = RetryStrategy.classify_error(exc)
        self.breaker.note_error()
        self.cost_manager.update_metrics(None, None, None, 0, None,
            error_kind=kind)
        if self.settings.log_attempts:
            _LOG.warning(
                f'LLM attempt #{attempts} failed. Kind: {kind}. Msg: {exc}')
        if (attempts > self.settings.max_retries or not RetryStrategy.
            is_retry_allowed(kind)):
            if self.settings.log_attempts:
                _LOG.error(f'LLM final failure. Kind: {kind}')
            raise exc
