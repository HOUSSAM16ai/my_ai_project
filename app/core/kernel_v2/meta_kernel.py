# app/core/kernel_v2/meta_kernel.py
"""
The Meta-Kernel, the central nervous system of Reality Kernel v2.
"""

from .state_engine import StateEngine
from .config_v2 import ConfigV2, get_settings
from .logging_spine import get_logger, setup_logging
from . import compat_collapse  # Import the module itself

class MetaKernel:
    """
    The orchestrator for the new reality.
    """
    def __init__(self):
        print("Reality Kernel v2 Initializing...")

        setup_logging()
        self.state: StateEngine = StateEngine()
        self.config: ConfigV2 = get_settings()
        self.logger = get_logger("reality_kernel")

        # Initialize the compatibility layer by passing 'self' (the kernel instance)
        compat_collapse.initialize_compat_layer(self)

        self.logger.info("Reality Kernel v2 is online and fully operational.")

_meta_kernel_instance = None

def get_kernel() -> MetaKernel:
    """
    Provides global access to the MetaKernel instance, creating it if needed.
    This lazy initialization helps prevent import-time issues.
    """
    global _meta_kernel_instance
    if _meta_kernel_instance is None:
        _meta_kernel_instance = MetaKernel()
    return _meta_kernel_instance

# Initialize on first call to get_kernel() instead of module load
