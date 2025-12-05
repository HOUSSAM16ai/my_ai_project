"""
Retry Strategy Module for LLM Services
======================================
Handles error classification and retry logic.
"""

import logging
import os
import random
import time

_LOG = logging.getLogger(__name__)

class RetryStrategy:
    """
    Singleton Retry Strategy logic.
    """

    @staticmethod
    def classify_error(exc: Exception) -> str:
        """
        Classify errors for intelligent retry and reporting.
        """
        msg = str(exc).lower()
        exc_type = type(exc).__name__.lower()

        # Server errors (5xx)
        if any(
            x in msg for x in ["server_error_500", "500", "internal server error", "502", "503", "504"]
        ):
            return "server_error"

        # Rate limiting
        if ("rate" in msg and "limit" in msg) or "429" in msg or "too many requests" in msg:
            return "rate_limit"

        # Authentication & Authorization errors
        if any(
            x in msg
            for x in [
                "authentication_error",
                "unauthorized",
                "api key",
                "invalid api key",
                "401",
                "403",
                "forbidden",
                "invalid_api_key",
            ]
        ):
            return "auth_error"

        # Timeout errors
        if "timeout" in msg or "timed out" in msg or "timeouterror" in exc_type:
            return "timeout"

        # Connection & Network errors
        if any(x in msg for x in ["connection", "network", "dns", "connect", "refused"]):
            return "network"

        # Parsing errors
        if ("parse" in msg or "json" in msg or "decode" in msg) and "error" in msg:
            return "parse"

        # Empty response errors
        if "empty" in msg or "no content" in msg or "null" in msg:
            return "empty_response"

        # Model-specific errors
        if "model" in msg and ("not found" in msg or "unavailable" in msg):
            return "model_error"

        return "unknown"

    @staticmethod
    def is_retry_allowed(kind: str) -> bool:
        """
        Determine if retry is allowed for this error type.
        """
        retry_on_auth = os.getenv("LLM_RETRY_ON_AUTH", "0") == "1"
        retry_on_parse = os.getenv("LLM_RETRY_ON_PARSE", "0") == "1"
        retry_on_empty = os.getenv("LLM_RETRY_ON_EMPTY", "1") == "1"

        if kind == "auth_error" and not retry_on_auth:
            return False

        if kind == "parse" and not retry_on_parse:
            return False

        if kind == "empty_response" and not retry_on_empty:
            return False

        retry_always = ["rate_limit", "network", "timeout", "server_error", "model_error"]
        if kind in retry_always:
            return True

        # For unknown errors, allow retry by default
        return True

    @staticmethod
    def get_backoff(attempt: int, base: float = 1.5, jitter: bool = True) -> float:
        """
        Calculate backoff time.
        Note: The original implementation used a cumulative multiplication.
        Here we calculate it stateless: base ** attempt?
        The original code did: backoff *= base.
        So for attempt 1 (before 1st retry): base.
        """
        # We'll mimic the original behavior roughly, but stateless is better.
        # Original: sleep_for = backoff; backoff *= base.
        # This implies exponential: initial * (base ^ (attempt-1))

        # However, to be perfectly safe and match the refactoring,
        # let's just use the current backoff value passed in by the caller loop
        # or implement a standard exponential backoff here.

        # Let's return just the jitter calculation part if needed,
        # or we rely on the loop to manage the state variable 'backoff'.
        pass
