import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """
    إعداد تكوين التسجيل الأساسي (Basic Logging Configuration).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    الحصول على مثيل المسجل (Logger Instance) بالاسم المحدد.
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger
