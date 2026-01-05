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
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TypeVar, cast, overload

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)

# ==================== DECORATORS ====================

def safe_execute(
    default_return: object | None = None,
    log_error: bool = True,
    error_message: str | None = None,
    raise_on_error: bool = False,
) -> Callable[[Callable[..., R]], Callable[..., R | object | None]]:
    """
    مُزخرف (Decorator) للتنفيذ الآمن للدوال مع معالجة تلقائية للأخطاء.

    يلغي الحاجة إلى كتل try-except المتكررة.

    Args:
        default_return: القيمة التي يتم إعادتها عند حدوث خطأ.
        log_error: هل يجب تسجيل الخطأ؟
        error_message: رسالة خطأ مخصصة.
        raise_on_error: هل يجب إعادة إثارة الاستثناء؟

    Returns:
        Callable: الدالة المزخرفة.
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R | object | None]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> R | object | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return _handle_safe_execute_error(
                    e, func, error_message, log_error, raise_on_error, default_return
                )

        return wrapper

    return decorator


def _handle_safe_execute_error(
    error: Exception,
    func: Callable[..., object],
    error_message: str | None,
    log_error: bool,
    raise_on_error: bool,
    default_return: object | None,
) -> object | None:
    """
    معالجة الأخطاء في مُزخرف safe_execute.
    """
    if log_error:
        msg = error_message or f"❌ Error in {func.__name__}"
        logger.error(f"{msg}: {error}", exc_info=True)
    if raise_on_error:
        raise error
    return default_return

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_retry: bool = True,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    مُزخرف (Decorator) لإعادة محاولة الدالة عند الفشل مع تأخير تصاعدي.

    Args:
        max_retries: الحد الأقصى لعدد المحاولات.
        delay: التأخير الأولي بين المحاولات (بالثواني).
        backoff: معامل مضاعفة التأخير بعد كل محاولة.
        exceptions: أنواع الاستثناءات التي يجب التقاطها.
        log_retry: هل يجب تسجيل محاولات الإعادة؟
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> R:
            return _execute_with_retry(
                func, args, kwargs, max_retries, delay, backoff, exceptions, log_retry
            )

        return wrapper

    return decorator


def _execute_with_retry(
    func: Callable[..., R],
    args: tuple[object, ...],
    kwargs: dict[str, object],
    max_retries: int,
    delay: float,
    backoff: float,
    exceptions: tuple[type[Exception], ...],
    log_retry: bool,
) -> R:
    """
    تنفيذ الدالة مع منطق إعادة المحاولة.
    """
    import time

    current_delay = delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                _log_retry_attempt(func, attempt, max_retries, e, log_retry)
                time.sleep(current_delay)
                current_delay *= backoff
            elif log_retry:
                logger.error(f"❌ Failed after {max_retries} retries: {func.__name__}")

    # All retries exhausted
    if last_exception:
        raise last_exception
    # Should not reach here if exceptions cover all errors
    raise RuntimeError("Unexpected retry flow")


def _log_retry_attempt(
    func: Callable[..., object], attempt: int, max_retries: int, error: Exception, log_retry: bool
) -> None:
    """
    تسجيل محاولة إعادة المحاولة.
    """
    if log_retry:
        logger.warning(f"⚠️ Retry {attempt + 1}/{max_retries} for {func.__name__}: {error}")

def suppress_errors(*exceptions: type[Exception], log_error: bool = False) -> Callable[[Callable[..., R]], Callable[..., R | None]]:
    """
    مُزخرف (Decorator) لتجاهل استثناءات محددة.

    Args:
        *exceptions: أنواع الاستثناءات التي يجب تجاهلها.
        log_error: هل يجب تسجيل الأخطاء المتجاهلة؟
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R | None]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> R | None:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.debug(f"🔇 Suppressed error in {func.__name__}: {e}")
                return None

        return wrapper

    return decorator

# ==================== CONTEXT MANAGERS ====================

@contextmanager
def safe_context(
    error_message: str = "Operation failed",
    default_return: object | None = None,
    log_error: bool = True,
    raise_on_error: bool = False,
) -> Generator[None, None, None]:
    """
    مدير سياق (Context Manager) لكتل التنفيذ الآمن.

    Args:
        error_message: الرسالة التي يتم تسجيلها عند الخطأ.
        default_return: القيمة التي يتم إعادتها (نظرياً) عند الخطأ - ملاحظة: Context managers لا يعيدون قيمة عند الاستثناء إلا إذا تم التعامل معه داخلياً.
        log_error: هل يجب تسجيل الخطأ؟
        raise_on_error: هل يجب إعادة إثارة الاستثناء؟
    """
    try:
        yield
    except Exception as e:
        if log_error:
            logger.error(f"❌ {error_message}: {e}", exc_info=True)
        if raise_on_error:
            raise e
        # Don't yield again, just pass

@contextmanager
def capture_errors(error_list: list[Exception] | None = None) -> Generator[None, None, None]:
    """
    مدير سياق لالتقاط الأخطاء دون تعطل البرنامج.

    Args:
        error_list: قائمة لإضافة الأخطاء الملتقطة إليها.
    """
    try:
        yield
    except Exception as e:
        if error_list is not None:
            error_list.append(e)
        logger.debug(f"🎣 Captured error: {e}")

# ==================== ERROR HANDLERS ====================

class ErrorHandler:
    """
    معالج أخطاء مركزي مع تسجيل ومقاييس.
    Centralized error handling with logging and metrics.
    """

    def __init__(self, service_name: str = "unknown"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"error_handler.{service_name}")
        self.error_count = 0

    def handle(
        self,
        error: Exception,
        context: dict[str, object] | None = None,
        severity: str = "error",
    ) -> None:
        """
        معالجة خطأ مع تسجيل ومقاييس.
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

    def wrap_function(self, func: Callable[..., R], default_return: R | None = None) -> Callable[..., R | None]:
        """
        تغليف دالة بمعالجة الأخطاء.
        """

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> R | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx: dict[str, object] = {"args": args, "kwargs": kwargs}
                self.handle(e, context=ctx)
                return default_return

        return wrapper

# ==================== UTILITY FUNCTIONS ====================

def log_exception(
    logger_instance: logging.Logger | None = None,
    message: str = "Exception occurred",
    level: str = "error",
) -> None:
    """
    تسجيل الاستثناء الحالي مع تتبع المكدس (Traceback).
    """
    log = logger_instance or logger
    log_func = getattr(log, level, log.error)
    log_func(f"{message}\n{traceback.format_exc()}")

def format_exception(error: Exception, include_traceback: bool = True) -> str:
    """
    تنسيق الاستثناء للعرض.
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if include_traceback:
        tb = traceback.format_exc()
        return f"{error_type}: {error_msg}\n\nTraceback:\n{tb}"

    return f"{error_type}: {error_msg}"

# ==================== EXPORTS ====================

__all__ = [
    "ErrorHandler",
    "capture_errors",
    "format_exception",
    "log_exception",
    "retry_on_failure",
    "safe_context",
    "safe_execute",
    "suppress_errors",
]
