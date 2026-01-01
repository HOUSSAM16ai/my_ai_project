"""
إطار معالجة الأخطاء (Error Handling Framework).

يوفر معالجة مركزية للأخطاء لتقليل استخدام try-except المفرط في الكود.
يستخدم decorators و context managers للحصول على كود نظيف ومتوافق مع DRY.

المبادئ (Principles):
- Harvard CS50 2025: توثيق عربي احترافي، صرامة الأنواع
- Berkeley SICP: Functional Core (decorators كدوال عليا)
- SOLID: Single Responsibility (كل decorator له مسؤولية واحدة)

الاستخدام (Usage):
    @safe_execute(default_return={})
    def risky_operation() -> None:
        return dangerous_call()
"""

import functools
import logging
import traceback
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar, cast

# Type variables for generic functions
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


logger = logging.getLogger(__name__)


# ==================== DECORATORS ====================


def safe_execute(
    default_return: Any = None,
    log_error: bool = True,
    error_message: str | None = None,
    raise_on_error: bool = False,
):
    """
    Decorator for safe function execution with automatic error handling.

    Eliminates the need for repetitive try-except blocks.

    Args:
        default_return: Value to return on error
        log_error: Whether to log the error
        error_message: Custom error message
        raise_on_error: Whether to re-raise the exception

    Example:
        @safe_execute(default_return={}, log_error=True)
        def risky_operation() -> None:
            return dangerous_call()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    msg = error_message or f"Error in {func.__name__}"
                    logger.error(f"{msg}: {e}", exc_info=True)
                if raise_on_error:
                    raise
                return default_return

        return cast(F, wrapper)

    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_retry: bool = True,
):
    """
    Decorator to retry function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        log_retry: Whether to log retry attempts

    Example:
        @retry_on_failure(max_retries=3, delay=1.0)
        def unstable_api_call() -> None:
            return external_service.call()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if log_retry:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    elif log_retry:
                        logger.error(f"Failed after {max_retries} retries: {func.__name__}")

            # All retries exhausted
            if last_exception:
                raise last_exception
            return None

        return cast(F, wrapper)

    return decorator


def suppress_errors(*exceptions: type[Exception], log_error: bool = False):
    """
    Decorator to suppress specific exceptions.

    Args:
        *exceptions: Exception types to suppress
        log_error: Whether to log suppressed errors

    Example:
        @suppress_errors(ValueError, KeyError, log_error=True)
        def parse_data(data):
            return data['key']  # Won't crash if key missing
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.debug(f"Suppressed error in {func.__name__}: {e}")
                return None

        return cast(F, wrapper)

    return decorator


# ==================== CONTEXT MANAGERS ====================


@contextmanager
def safe_context(
    error_message: str = "Operation failed",
    default_return: Any = None,
    log_error: bool = True,
    raise_on_error: bool = False,
):
    """
    Context manager for safe execution blocks.

    Args:
        error_message: Message to log on error
        default_return: Value to yield on error
        log_error: Whether to log the error
        raise_on_error: Whether to re-raise the exception

    Example:
        with safe_context("Database operation failed", default_return=[]):
            results = db.query(Model).all()
        # results will be [] if error occurs
    """
    try:
        yield
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {e}", exc_info=True)
        if raise_on_error:
            raise
        # Don't yield again, just pass


@contextmanager
def capture_errors(error_list: list[Exception] | None = None):
    """
    Context manager to capture errors without crashing.

    Args:
        error_list: List to append captured errors to

    Example:
        errors = []
        with capture_errors(errors):
            dangerous_operation()
        # Check errors list after
    """
    try:
        yield
    except Exception as e:
        if error_list is not None:
            error_list.append(e)
        logger.debug(f"Captured error: {e}")


# ==================== ERROR HANDLERS ====================


class ErrorHandler:
    """Centralized error handling with logging and metrics."""

    def __init__(self, service_name: str = "unknown"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"error_handler.{service_name}")
        self.error_count = 0

    def handle(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        """
        Handle an error with logging and metrics.

        Args:
            error: The exception to handle
            context: Additional context information
            severity: Log severity level
        """
        self.error_count += 1

        log_func = getattr(self.logger, severity, self.logger.error)

        context_str = ""
        if context:
            context_str = f" | Context: {context}"

        log_func(
            f"[{self.service_name}] Error #{self.error_count}: "
            f"{type(error).__name__}: {error}{context_str}"
        )

    def wrap_function(self, func: F, default_return: Any = None) -> F:
        """
        Wrap a function with error handling.

        Args:
            func: Function to wrap
            default_return: Value to return on error

        Returns:
            Wrapped function
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle(e, context={"args": args, "kwargs": kwargs})
                return default_return

        return cast(F, wrapper)


# ==================== UTILITY FUNCTIONS ====================


def log_exception(
    logger_instance: logging.Logger | None = None,
    message: str = "Exception occurred",
    level: str = "error",
) -> None:
    """
    Log current exception with traceback.

    Args:
        logger_instance: Logger to use (or default)
        message: Message to log
        level: Log level
    """
    log = logger_instance or logger
    log_func = getattr(log, level, log.error)
    log_func(f"{message}\n{traceback.format_exc()}")


def format_exception(error: Exception, include_traceback: bool = True) -> str:
    """
    Format exception for display.

    Args:
        error: Exception to format
        include_traceback: Whether to include full traceback

    Returns:
        Formatted error string
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if include_traceback:
        tb = traceback.format_exc()
        return f"{error_type}: {error_msg}\n\nTraceback:\n{tb}"

    return f"{error_type}: {error_msg}"


# ==================== EXPORTS ====================

__all__ = [
    # Classes
    "ErrorHandler",
    # Context managers
    "capture_errors",
    # Utilities
    "format_exception",
    "log_exception",
    # Decorators
    "retry_on_failure",
    "safe_context",
    "safe_execute",
    "suppress_errors",
]


# ==================== USAGE EXAMPLES ====================
"""
# Example 1: Replace try-except with decorator
# Before:
def fetch_data() -> None:
    try:
        return api.get_data()
    except Exception as e:
        logger.error(f"Failed to fetch: {e}")
        return {}

# After:
@safe_execute(default_return={}, log_error=True)
def fetch_data() -> None:
    return api.get_data()


# Example 2: Retry on failure
# Before:
def unreliable_operation() -> None:
    for attempt in range(3):
        try:
            return external_call()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1)

# After:
@retry_on_failure(max_retries=3, delay=1.0)
def unreliable_operation() -> None:
    return external_call()


# Example 3: Context manager for safe blocks
# Before:
try:
    result = db.query(Model).all()
except Exception as e:
    logger.error(f"Query failed: {e}")
    result = []

# After:
with safe_context("Query failed", default_return=[]):
    result = db.query(Model).all()
"""
