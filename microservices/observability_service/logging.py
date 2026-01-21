"""
تسجيل السجلات لخدمة المراقبة.

يضمن وضوح الرسائل مع الالتزام بإعدادات الخدمة.
"""

import logging
import sys

from microservices.observability_service.settings import get_settings


def setup_logging(service_name: str | None = None) -> None:
    """تهيئة السجلات لخدمة المراقبة حسب الإعدادات المحلية."""

    settings = get_settings()
    log_level = settings.LOG_LEVEL.upper()
    svc_name = service_name or settings.SERVICE_NAME

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(service_name)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.handlers:
        root_logger.handlers = []

    root_logger.addHandler(handler)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: object, **kwargs: object) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.service_name = svc_name  # type: ignore
        return record

    logging.setLogRecordFactory(record_factory)


def get_logger(name: str) -> logging.Logger:
    """الحصول على Logger باسم محدد."""

    return logging.getLogger(name)
