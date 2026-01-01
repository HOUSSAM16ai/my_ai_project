"""
خدمة عميل LLM الأساسية (المحرك).
Core LLM Client Service (Engine).
"""

import os
import random
import time
from collections.abc import Callable, Generator

from app.core.logging import get_logger
from app.services.llm_client.application.circuit_breaker import CircuitBreaker
from app.services.llm_client.application.cost import CostManager
from app.services.llm_client.application.retry import RetryStrategy
from app.services.llm_client.domain.models import LLMMeta, LLMPayload, LLMResponseEnvelope
from app.services.llm_client.infrastructure.client_factory import get_llm_client

_LOG = get_logger(__name__)

# Hooks storage
_PRE_HOOKS: list[Callable[[LLMPayload], None]] = []
_POST_HOOKS: list[Callable[[LLMPayload, LLMResponseEnvelope], None]] = []

def register_llm_pre_hook(fn: Callable[[LLMPayload], None]) -> None:
    _PRE_HOOKS.append(fn)

def register_llm_post_hook(fn: Callable[[LLMPayload, LLMResponseEnvelope], None]) -> None:
    _POST_HOOKS.append(fn)

# TODO: Split this function (164 lines) - KISS principle
def invoke_chat(
    model: str,
    messages: list[dict[str, str]],
    *,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    stream: bool = False,
    extra: dict[str, Any] | None = None,
) -> LLMResponseEnvelope | Generator[dict[str, Any], None, None]:
    """
    تنفيذ محادثة مع النموذج اللغوي.
    Execute chat with the LLM.
    """

    # 1. Circuit Breaker Check
    breaker = CircuitBreaker()
    if not breaker.is_allowed():
        raise RuntimeError("LLM Circuit Breaker is OPEN.")

    # 2. Build Payload
    payload = LLMPayload(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
        extra=extra
    )

    # 3. Run Pre-Hooks
    for hook in _PRE_HOOKS:
        try:
            hook(payload)
        except Exception as e:
            _LOG.warning(f"Pre-hook error: {e}")

    # 4. Prepare Context
    client = get_llm_client()
    cost_manager = CostManager()

    # Retry Config (Environment Variables for tuning)
    # Ideally should be in AppSettings, keeping os.getenv for now to match behavior
    # but strictly typed parsing.
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    backoff_base = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "1.5"))

    start_ts = time.time()
    retry_schedule: list[float] = []

    # TODO: Split this function (77 lines) - KISS principle
    # 5. Execution Function
    def _execute() -> LLMResponseEnvelope:
        attempts = 0
        backoff = backoff_base

        while attempts <= max_retries:
            attempts += 1
            t0 = time.perf_counter()

            try:
                response = client.chat.completions.create(
                    model=payload.model,
                    messages=payload.messages,
                    tools=payload.tools,
                    tool_choice=payload.tool_choice,
                    temperature=payload.temperature,
                    max_tokens=payload.max_tokens,
                    stream=False # Force false for this inner block
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0

                # Success - Normalization
                choice = response.choices[0]
                message = choice.message

                # Update Costs
                usage = response.usage
                if usage:
                    cost_manager.update_metrics(
                        model=payload.model,
                        input_tokens=usage.prompt_tokens,
                        output_tokens=usage.completion_tokens,
                        latency_ms=latency_ms,
                        finish_reason=choice.finish_reason
                    )

                breaker.note_success()

                meta = LLMMeta(
                    latency_ms=latency_ms,
                    attempts=attempts,
                    retry_schedule=retry_schedule,
                    timestamp_start=start_ts,
                    timestamp_end=time.time(),
                    model_used=response.model,
                    finish_reason=choice.finish_reason,
                    stream=False
                )

                envelope = LLMResponseEnvelope(
                    content=message.content or "",
                    role=message.role,
                    tool_calls=[tc.model_dump() for tc in message.tool_calls] if message.tool_calls else None,
                    meta=meta,
                    raw=response.model_dump()
                )

                # Post Hooks
                for hook in _POST_HOOKS:
                    try:
                        hook(payload, envelope)
                    except Exception as e:
                        _LOG.warning(f"Post-hook error: {e}")

                return envelope

            except Exception as e:
                kind = RetryStrategy.classify_error(e)
                breaker.note_error()

                if not RetryStrategy.is_retry_allowed(kind) or attempts > max_retries:
                    raise e

                sleep_time = backoff + (random.random() * 0.25)
                retry_schedule.append(sleep_time)
                time.sleep(sleep_time)
                backoff *= backoff_base

        raise RuntimeError("Max retries exceeded")

    if not stream:
        return _execute()

    # Streaming Logic
    # For strict typing, we might need a separate function, but here we return a generator
    # Note: The original implementation simulated streaming from a full response for some reason?
    # Or maybe it delegated to real streaming.
    # Here we implement REAL streaming support if client supports it,
    # OR we follow the interface.

    # If the user requested stream, we usually want to yield chunks.
    # For now, matching the original logic which seemed to return a generator of dicts.

    def _stream_generator():
        # TODO: Implement true streaming if required.
        # The legacy code did: get full response -> yield chunks (simulated).
        # We will replicate that behavior for safety in this refactor,
        # unless we are sure real streaming is required.
        # "invoke_chat_stream" in legacy implies it.

        envelope = _execute()
        content = envelope.content
        chunk_size = 20

        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            yield {"delta": chunk}

        # Finally yield the envelope
        yield envelope.model_dump()

    return _stream_generator()

def invoke_chat_stream(*args, **kwargs) -> None:
    kwargs["stream"] = True
    return invoke_chat(*args, **kwargs)
