"""
CLI Logging - تكوين التسجيل لأوامر سطر الأوامر.
"""
import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.settings import AppSettings

def create_logger(settings: "AppSettings") -> logging.Logger:
    """
    إنشاء مسجل (Logger) للاستخدام في سطر الأوامر.
    """
    logger = logging.getLogger("cogniforge.cli")
    logger.setLevel(settings.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
