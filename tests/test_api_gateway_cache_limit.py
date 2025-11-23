
import pytest
import threading
from app.services.api_gateway_service import IntelligentCache

def test_cache_oversized_item_prevention():
    """
    Verifies that inserting an item larger than the total cache size
    does not cause an infinite loop and does not store the item.
    """
    # 1. Setup cache with small size (1 MB)
    cache = IntelligentCache(max_size_mb=1)

    request_data = {"key": "test_oversized"}

    # 2. Create oversized data (> 1 MB)
    # 1.5 MB string
    large_string = "x" * (int(1.5 * 1024 * 1024))
    response_data = {"data": large_string}

    # 3. Attempt to put into cache
    # Use a thread with timeout to detect infinite loop regression
    done_event = threading.Event()

    def run_put():
        cache.put(request_data, response_data)
        done_event.set()

    t = threading.Thread(target=run_put)
    t.start()

    # Wait max 2 seconds
    is_done = done_event.wait(timeout=2.0)

    if not is_done:
        pytest.fail("IntelligentCache.put() hung (possible infinite loop) on oversized item.")

    t.join(timeout=1)

    # 4. Verify item was NOT stored
    cached_val = cache.get(request_data)
    assert cached_val is None, "Oversized item should not be cached"

    # 5. Verify cache stats
    stats = cache.get_stats()
    # Cache size should be 0 because nothing fit
    assert stats["entry_count"] == 0
    assert stats["cache_size_mb"] == 0.0

def test_cache_eviction_safety():
    """
    Verifies that we can fill the cache and then evict correctly
    without infinite loops when adding new items.
    """
    # 1MB cache
    cache = IntelligentCache(max_size_mb=1)

    # Add 0.6 MB item
    data1 = "a" * (int(0.6 * 1024 * 1024))
    cache.put({"k": 1}, {"d": data1})

    assert cache.get({"k": 1}) is not None

    # Add another 0.6 MB item -> should evict first one
    data2 = "b" * (int(0.6 * 1024 * 1024))
    cache.put({"k": 2}, {"d": data2})

    assert cache.get({"k": 2}) is not None
    assert cache.get({"k": 1}) is None # Evicted
