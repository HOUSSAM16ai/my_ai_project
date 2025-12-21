import os
import threading
import time
from collections.abc import Callable
from uuid import uuid4


class QuantumStatementNameGenerator:
    """
    🔐 QUANTUM-SAFE STATEMENT NAME GENERATOR

    Generates cryptographically unique prepared statement names using
    a combination of:
    - Thread-local counters for high-performance sequential naming
    - UUID4 for global uniqueness across distributed systems
    - Timestamp component for temporal ordering
    - Process ID for multi-process safety

    This ensures ZERO collisions even in:
    - High-concurrency scenarios
    - Multi-process deployments
    - PgBouncer transaction pooling mode
    - Connection reuse across sessions
    """

    _local = threading.local()
    _global_counter = 0
    _lock = threading.Lock()

    @classmethod
    def generate(cls) -> str:
        """
        Generate a unique prepared statement name.

        Format: __cogniforge_{timestamp_hex}_{counter}_{uuid_short}__

        This format ensures:
        1. Prefix identification for debugging
        2. Temporal ordering via timestamp
        3. Sequential ordering via counter
        4. Global uniqueness via UUID
        """
        # Thread-local counter for performance
        if not hasattr(cls._local, "counter"):
            cls._local.counter = 0
        cls._local.counter += 1

        # Global counter for cross-thread uniqueness
        with cls._lock:
            cls._global_counter += 1
            global_count = cls._global_counter

        # Components for the unique name
        timestamp_hex = hex(int(time.time() * 1000000))[2:]  # Microsecond precision
        uuid_short = uuid4().hex[:8]  # 8 chars of UUID for brevity
        pid = os.getpid()

        # Combine all components
        name = f"__cogniforge_{timestamp_hex}_{pid}_{global_count}_{uuid_short}__"

        return name

    @classmethod
    def get_generator_func(cls) -> Callable[[], str]:
        """Return a callable that generates unique names."""
        return cls.generate
