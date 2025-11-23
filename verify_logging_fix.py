import logging
import sys
from app.core.kernel_v2.logging_spine import setup_logging, get_logger

def test_logging_setup():
    # Ensure no handlers initially (simulating app start)
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)

    # Verify setup_logging configures handlers
    setup_logging.cache_clear() # Clear cache for this test
    setup_logging()

    assert len(root.handlers) > 0, "Logging should be configured"
    print("Logging configured successfully")

    # Test idempotency (cache)
    handlers_count = len(root.handlers)
    setup_logging()
    assert len(root.handlers) == handlers_count, "Should not add more handlers"

def test_logging_respects_existing():
    # Reset
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)

    # Add a dummy handler
    h = logging.NullHandler()
    root.addHandler(h)

    # Run setup
    setup_logging.cache_clear()
    setup_logging()

    # Should NOT have reconfigured (based on my fix)
    # The 'stdout' handler from config should NOT be present if we skipped
    # But wait, my fix returns if ANY handler is present.
    # So it should just have the NullHandler.

    handlers = root.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.NullHandler)
    print("Respected existing configuration")

if __name__ == "__main__":
    test_logging_setup()
    test_logging_respects_existing()
