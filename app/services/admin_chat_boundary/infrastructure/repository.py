"""
In-Memory Repository for AdminChatBoundary
"""

import threading
from collections import deque


class InMemoryAdminChatBoundaryRepository:
    """In-memory implementation"""

    def __init__(self, max_size: int = 10000):
        self._data = deque(maxlen=max_size)
        self._lock = threading.RLock()

    # Add your repository methods here
