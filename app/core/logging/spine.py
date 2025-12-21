import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO") -> None:
    """
    Setup basic logging configuration.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger
