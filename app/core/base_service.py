"""
خدمة قاعدية (Base Service).

يوفر وظائف مشتركة لجميع الخدمات لتطبيق مبدأ DRY.

المعايير:
- Harvard CS50 2025: توثيق عربي شامل
- Berkeley SICP: Functional Core, Imperative Shell
- SOLID: Single Responsibility Principle
"""

import logging


class BaseService:
    """
    خدمة قاعدية لجميع خدمات التطبيق.

    توفر وظائف مشتركة مثل التسجيل والتحقق من الصحة.
    """

    def __init__(self, service_name: str | None = None):
        """
        تهيئة الخدمة.

        Args:
            service_name: اسم الخدمة (اختياري)
        """
        self._service_name = service_name or self.__class__.__name__
        self._logger = logging.getLogger(f"{__name__}.{self._service_name}")

    def _log_info(self, message: str, **kwargs: dict[str, str | int | bool]) -> None:
        """تسجيل رسالة معلومات."""
        self._logger.info(message, extra=kwargs)

    def _log_error(self, message: str, exc: Exception | None = None, **kwargs: dict[str, str | int | bool]) -> None:
        """تسجيل رسالة خطأ."""
        if exc:
            self._logger.error(message, exc_info=exc, extra=kwargs)
        else:
            self._logger.error(message, extra=kwargs)

    def _log_warning(self, message: str, **kwargs: dict[str, str | int | bool]) -> None:
        """تسجيل رسالة تحذير."""
        self._logger.warning(message, extra=kwargs)

    def _log_debug(self, message: str, **kwargs: dict[str, str | int | bool]) -> None:
        """تسجيل رسالة تصحيح."""
        self._logger.debug(message, extra=kwargs)

    def _validate_not_none(self, value: dict[str, str | int | bool], name: str) -> None:
        """
        التحقق من أن القيمة ليست None.

        Args:
            value: القيمة المراد التحقق منها
            name: اسم المتغير

        Raises:
            ValueError: إذا كانت القيمة None
        """
        if value is None:
            raise ValueError(f"{name} cannot be None")

    def _validate_not_empty(self, value: str, name: str) -> None:
        """
        التحقق من أن النص ليس فارغاً.

        Args:
            value: النص المراد التحقق منه
            name: اسم المتغير

        Raises:
            ValueError: إذا كان النص فارغاً
        """
        if not value or not value.strip():
            raise ValueError(f"{name} cannot be empty")

    def _validate_positive(self, value: int | float, name: str) -> None:
        """
        التحقق من أن الرقم موجب.

        Args:
            value: الرقم المراد التحقق منه
            name: اسم المتغير

        Raises:
            ValueError: إذا كان الرقم سالباً أو صفراً
        """
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")
