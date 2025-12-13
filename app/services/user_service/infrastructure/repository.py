"""
In-Memory Repository for UserService
"""

import threading
from collections import deque


class InMemoryUserServiceRepository:
    """In-memory implementation"""

    def __init__(self, max_size: int = 10000):
        self._data = deque(maxlen=max_size)
        self._lock = threading.RLock()

    # Add your repository methods here
