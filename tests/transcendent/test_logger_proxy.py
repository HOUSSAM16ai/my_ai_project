import logging
from app.core.deps import get_logger

def test_logger_proxy():
    """
    Tests that get_logger() can be used to log messages.
    """
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)

    # This is a simple test to ensure the logger can be instantiated
    # without a Flask context. A more advanced test would capture
    # stdout/stderr to check the log output.
    logger.info("This is a test log message.")
