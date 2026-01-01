"""
CS61 Memory Manager | مدير الذاكرة
====================================

Memory management utilities following CS61 principles:
- Memory pooling
- Bounded collections
- Memory leak detection
- Resource tracking

إدارة الذاكرة وفق مبادئ CS61
"""
from __future__ import annotations

import gc
import logging
import weakref
from collections import deque
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Generic, TypeVar, Iterator

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ==============================================================================
# CS61: Bounded Collections (مجموعات محدودة الحجم)
# ==============================================================================

class BoundedList(Generic[T]):
    """
    قائمة محدودة الحجم (Bounded list with automatic eviction).
    
    CS61 Principle: Prevent unbounded memory growth.
    Uses deque with maxlen for O(1) append and automatic LRU eviction.
    
    Example:
        recent_logs = BoundedList[str](maxlen=100)
        recent_logs.append("log entry")  # Old entries auto-removed
    """
    
    def __init__(self, maxlen: int = 1000):
        """
        Args:
            maxlen: Maximum number of elements
        """
        if maxlen <= 0:
            raise ValueError("maxlen must be positive")
        
        self._data: deque[T] = deque(maxlen=maxlen)
        self._maxlen = maxlen
    
    def append(self, item: T) -> None:
        """إضافة عنصر (Append item, auto-evict if full)."""
        self._data.append(item)
    
    def extend(self, items: list[T]) -> None:
        """إضافة عدة عناصر (Extend with multiple items)."""
        self._data.extend(items)
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self) -> Iterator[T]:
        return iter(self._data)
    
    def __getitem__(self, index: int) -> T:
        return self._data[index]
    
    @property
    def maxlen(self) -> int:
        """الحد الأقصى للحجم (Maximum capacity)."""
        return self._maxlen
    
    @property
    def is_full(self) -> bool:
        """هل القائمة ممتلئة؟ (Is list at capacity?)"""
        return len(self._data) >= self._maxlen
    
    def clear(self) -> None:
        """مسح جميع العناصر (Clear all items)."""
        self._data.clear()
    
    def to_list(self) -> list[T]:
        """تحويل إلى قائمة عادية (Convert to regular list)."""
        return list(self._data)


class BoundedDict(Generic[T]):
    """
    قاموس محدود الحجم مع LRU (Bounded dictionary with LRU eviction).
    
    CS61 Principle: Fixed memory footprint cache.
    
    Example:
        cache = BoundedDict[User](maxsize=100)
        cache['user_123'] = user  # LRU eviction when full
    """
    
    def __init__(self, maxsize: int = 1000):
        """
        Args:
            maxsize: Maximum number of key-value pairs
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        
        self._data: dict[str, T] = {}
        self._access_order: deque[str] = deque()
        self._maxsize = maxsize
    
    def __setitem__(self, key: str, value: T) -> None:
        """إضافة أو تحديث عنصر (Set item with LRU tracking)."""
        # Update existing key
        if key in self._data:
            self._access_order.remove(key)
        # Evict oldest if at capacity
        elif len(self._data) >= self._maxsize:
            oldest_key = self._access_order.popleft()
            del self._data[oldest_key]
        
        self._data[key] = value
        self._access_order.append(key)
    
    def __getitem__(self, key: str) -> T:
        """الحصول على عنصر (Get item and update LRU)."""
        value = self._data[key]
        # Update access order
        self._access_order.remove(key)
        self._access_order.append(key)
        return value
    
    def get(self, key: str, default: T | None = None) -> T | None:
        """الحصول على عنصر مع قيمة افتراضية (Get with default)."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def __len__(self) -> int:
        return len(self._data)
    
    def clear(self) -> None:
        """مسح جميع العناصر (Clear all items)."""
        self._data.clear()
        self._access_order.clear()
    
    @property
    def maxsize(self) -> int:
        """الحد الأقصى للحجم (Maximum capacity)."""
        return self._maxsize


# ==============================================================================
# CS61: Object Pooling (تجميع الكائنات)
# ==============================================================================

class ObjectPool(Generic[T]):
    """
    مُجمِّع الكائنات (Object pool for reusing expensive objects).
    
    CS61 Principle: Reduce allocation/deallocation overhead.
    Useful for database connections, HTTP clients, etc.
    
    Example:
        pool = ObjectPool(factory=create_db_connection, size=10)
        with pool.acquire() as conn:
            conn.execute(query)
    """
    
    def __init__(self, factory: callable, size: int = 10):
        """
        Args:
            factory: Function to create new objects
            size: Maximum pool size
        """
        self._factory = factory
        self._size = size
        self._pool: deque[T] = deque()
        self._in_use = 0
    
    @contextmanager
    def acquire(self) -> Iterator[T]:
        """
        الحصول على كائن من المجمِّع (Acquire object from pool).
        
        Automatically returns object to pool when done.
        """
        # Try to get from pool
        if self._pool:
            obj = self._pool.popleft()
        # Create new if pool empty and under limit
        elif self._in_use < self._size:
            obj = self._factory()
        else:
            raise RuntimeError(f"Pool exhausted (size={self._size})")
        
        self._in_use += 1
        
        try:
            yield obj
        finally:
            # Return to pool
            self._pool.append(obj)
            self._in_use -= 1
    
    def __len__(self) -> int:
        """عدد الكائنات المتاحة (Number of available objects)."""
        return len(self._pool)
    
    @property
    def in_use_count(self) -> int:
        """عدد الكائنات قيد الاستخدام (Number of objects in use)."""
        return self._in_use


# ==============================================================================
# CS61: Memory Leak Detection (كشف تسريبات الذاكرة)
# ==============================================================================

class MemoryTracker:
    """
    متتبع الذاكرة (Memory leak detector).
    
    CS61 Principle: Monitor object lifecycles and detect leaks.
    
    Example:
        tracker = MemoryTracker()
        tracker.track(expensive_object, "ExpensiveObject")
        # Later: check if object was properly cleaned up
        tracker.print_report()
    """
    
    def __init__(self):
        """Initialize tracker with weak references."""
        self._tracked: dict[str, list[weakref.ref]] = {}
    
    def track(self, obj: Any, category: str = "default") -> None:
        """
        تتبع كائن (Track an object for memory leak detection).
        
        Args:
            obj: Object to track
            category: Category name for grouping
        """
        if category not in self._tracked:
            self._tracked[category] = []
        
        # Use weak reference (doesn't prevent garbage collection)
        # Note: Some built-in types (dict, list, str) don't support weak refs
        try:
            self._tracked[category].append(weakref.ref(obj))
        except TypeError:
            # For objects that don't support weak refs, wrap in a class
            class WeakRefWrapper:
                def __init__(self, obj):
                    self._obj = obj
                def __call__(self):
                    return self._obj
            self._tracked[category].append(weakref.ref(WeakRefWrapper(obj)))
    
    def get_alive_count(self, category: str) -> int:
        """
        عدد الكائنات الحية (Count objects still alive).
        
        Args:
            category: Category to check
            
        Returns:
            Number of tracked objects still in memory
        """
        if category not in self._tracked:
            return 0
        
        # Count references that are still alive
        return sum(1 for ref in self._tracked[category] if ref() is not None)
    
    def print_report(self) -> None:
        """طباعة تقرير تسريبات الذاكرة (Print memory leak report)."""
        print("\n" + "=" * 80)
        print("CS61 MEMORY LEAK REPORT | تقرير تسريبات الذاكرة")
        print("=" * 80)
        
        for category, refs in self._tracked.items():
            alive = sum(1 for ref in refs if ref() is not None)
            total = len(refs)
            leak_rate = (alive / total * 100) if total > 0 else 0
            
            status = "✅ OK" if leak_rate < 10 else "⚠️ WARNING" if leak_rate < 50 else "🔴 LEAK"
            
            print(f"\n{status} {category}")
            print(f"   Tracked: {total}")
            print(f"   Alive:   {alive}")
            print(f"   Leak:    {leak_rate:.1f}%")
        
        print("\n" + "=" * 80 + "\n")
    
    def cleanup(self) -> None:
        """تنظيف المراجع الميتة (Clean up dead references)."""
        for category in self._tracked:
            self._tracked[category] = [
                ref for ref in self._tracked[category]
                if ref() is not None
            ]


# ==============================================================================
# CS61: Memory Utilities (أدوات الذاكرة)
# ==============================================================================

def force_garbage_collection() -> dict[str, int]:
    """
    فرض تشغيل جامع القمامة (Force garbage collection).
    
    CS61 Principle: Manual memory management in Python.
    
    Returns:
        Statistics about collected objects
    """
    collected = {
        'gen0': gc.collect(0),  # Young generation
        'gen1': gc.collect(1),  # Middle generation
        'gen2': gc.collect(2),  # Old generation
    }
    
    total = sum(collected.values())
    logger.info(f"Garbage collection: {total} objects collected")
    
    return collected


def get_object_count_by_type() -> dict[str, int]:
    """
    عدد الكائنات حسب النوع (Count objects by type).
    
    CS61 Principle: Understand memory composition.
    
    Returns:
        Dictionary mapping type names to counts
    """
    from collections import Counter
    
    # Get all objects
    all_objects = gc.get_objects()
    
    # Count by type
    type_counts = Counter(type(obj).__name__ for obj in all_objects)
    
    # Return top 20
    return dict(type_counts.most_common(20))


@lru_cache(maxsize=128)
def cached_computation(key: str) -> Any:
    """
    مثال على استخدام LRU cache (Example of LRU caching).
    
    CS61 Principle: Memory-bounded caching with automatic eviction.
    Cache size limited to 128 entries using LRU policy.
    """
    # Expensive computation here
    pass


# ==============================================================================
# Exports
# ==============================================================================

__all__ = [
    'BoundedList',
    'BoundedDict',
    'ObjectPool',
    'MemoryTracker',
    'force_garbage_collection',
    'get_object_count_by_type',
    'cached_computation',
]
