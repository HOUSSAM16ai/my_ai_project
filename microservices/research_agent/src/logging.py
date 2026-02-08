"""وحدة تسجيل محلية لخدمة البحث."""

from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    """تهيئة التسجيل وفق بيئة التشغيل وبشكل مبسط."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """يعيد كائن مسجل جاهز للاستخدام."""
    setup_logging()
    return logging.getLogger(name)
