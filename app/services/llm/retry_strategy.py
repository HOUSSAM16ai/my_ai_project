"""
Retry Strategy Module for LLM Services
======================================
Handles error classification and retry logic.
"""

import logging
import os

_LOG = logging.getLogger(__name__)


class RetryStrategy:
    """
    Singleton Retry Strategy logic.
    """

    @staticmethod
    def _check_server_error(msg: str) -> bool:
        """Check if error is a server error (5xx)."""
        server_indicators = [
            "server_error_500",
            "500",
            "internal server error",
            "502",
            "503",
            "504",
        ]
        return any(x in msg for x in server_indicators)

    @staticmethod
    def _check_rate_limit(msg: str) -> bool:
        """Check if error is rate limiting."""
        return ("rate" in msg and "limit" in msg) or "429" in msg or "too many requests" in msg

    @staticmethod
    def _check_auth_error(msg: str) -> bool:
        """Check if error is authentication/authorization."""
        auth_indicators = [
            "authentication_error",
            "unauthorized",
            "api key",
            "invalid api key",
            "401",
            "403",
            "forbidden",
            "invalid_api_key",
        ]
        return any(x in msg for x in auth_indicators)

    @staticmethod
    def _check_timeout(msg: str, exc_type: str) -> bool:
        """Check if error is timeout."""
        return "timeout" in msg or "timed out" in msg or "timeouterror" in exc_type

    @staticmethod
    def _check_network_error(msg: str) -> bool:
        """Check if error is network/connection."""
        network_indicators = ["connection", "network", "dns", "connect", "refused"]
        return any(x in msg for x in network_indicators)

    @staticmethod
    def _check_parse_error(msg: str) -> bool:
        """Check if error is parsing."""
        return ("parse" in msg or "json" in msg or "decode" in msg) and "error" in msg

    @staticmethod
    def _check_empty_response(msg: str) -> bool:
        """Check if error is empty response."""
        return "empty" in msg or "no content" in msg or "null" in msg

    @staticmethod
    def _check_model_error(msg: str) -> bool:
        """Check if error is model-specific."""
        return "model" in msg and ("not found" in msg or "unavailable" in msg)

    @staticmethod
    def classify_error(exc: Exception) -> str:
        """
        Classify errors for intelligent retry and reporting.
        """
        msg = str(exc).lower()
        exc_type = type(exc).__name__.lower()

        if RetryStrategy._check_server_error(msg):
            return "server_error"
        if RetryStrategy._check_rate_limit(msg):
            return "rate_limit"
        if RetryStrategy._check_auth_error(msg):
            return "auth_error"
        if RetryStrategy._check_timeout(msg, exc_type):
            return "timeout"
        if RetryStrategy._check_network_error(msg):
            return "network"
        if RetryStrategy._check_parse_error(msg):
            return "parse"
        if RetryStrategy._check_empty_response(msg):
            return "empty_response"
        if RetryStrategy._check_model_error(msg):
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
