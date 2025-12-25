"""
أدوات التسجيل (Logging Utilities).

توفر دوال مساعدة للتسجيل لتطبيق مبدأ DRY.

المعايير:
- Harvard CS50 2025: توثيق عربي شامل
- DRY: Don't Repeat Yourself
- KISS: Keep It Simple, Stupid
"""

import logging
from typing import Any


def get_logger(name: str | None = None) -> logging.Logger:
    """
    الحصول على مسجل (Logger) بالاسم المحدد.
    
    Args:
        name: اسم المسجل (اختياري، يستخدم __name__ افتراضياً)
        
    Returns:
        logging.Logger: مسجل جاهز للاستخدام
    """
    return logging.getLogger(name or __name__)


def log_function_call(logger: logging.Logger, func_name: str, **kwargs: Any) -> None:
    """
    تسجيل استدعاء دالة مع المعاملات.
    
    Args:
        logger: المسجل
        func_name: اسم الدالة
        **kwargs: معاملات الدالة
    """
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_exception(
    logger: logging.Logger, 
    message: str, 
    exc: Exception,
    **context: Any
) -> None:
    """
    تسجيل استثناء مع السياق.
    
    Args:
        logger: المسجل
        message: رسالة الخطأ
        exc: الاستثناء
        **context: سياق إضافي
    """
    logger.error(
        f"{message}: {exc}",
        exc_info=exc,
        extra={"context": context}
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **metrics: Any
) -> None:
    """
    تسجيل أداء عملية.
    
    Args:
        logger: المسجل
        operation: اسم العملية
        duration_ms: المدة بالميلي ثانية
        **metrics: مقاييس إضافية
    """
    metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
    logger.info(
        f"Performance: {operation} took {duration_ms:.2f}ms",
        extra={"duration_ms": duration_ms, "metrics": metrics}
    )
