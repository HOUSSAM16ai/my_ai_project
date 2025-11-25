import logging

from app.core.kernel_v2.logging_spine import setup_logging


# Verify logging fix
def test_logging_setup():
    """
    Verify that setup_logging is idempotent and doesn't crash.
    """
    setup_logging()
    logger = logging.getLogger("test_logger")
    logger.info("Logging verification test")
    assert True
