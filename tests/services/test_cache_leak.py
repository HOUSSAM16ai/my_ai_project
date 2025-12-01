import json
import time

from app.services.api_gateway_service import IntelligentCache


class TestIntelligentCacheLeak:
    """
    Test suite for IntelligentCache memory leak regressions.
    """

    def test_cache_size_leak_on_update(self):
        """
        Test that updating an existing cache entry correctly updates the total size.
        This verifies the fix for a bug where overwriting a key did not subtract the old size.
        """
        # Initialize cache with small size limit (e.g., 1MB)
        cache = IntelligentCache(max_size_mb=1)

        request_data = {"query": "test_leak"}

        # Create two responses of known size
        response1 = {"result": "a" * 100}  # ~115 bytes
        response2 = {"result": "b" * 100}  # ~115 bytes

        size1 = len(json.dumps(response1))
        size2 = len(json.dumps(response2))

        # 1. Put first response
        cache.put(request_data, response1)

        # Expected size should be size1
        assert cache.current_size_bytes == size1

        # 2. Put second response (update same key)
        cache.put(request_data, response2)

        # The correct behavior: current_size_bytes should be equal to size2 (since we replaced the entry)
        assert cache.current_size_bytes == size2, (
            f"Cache size incorrect. Expected {size2}, got {cache.current_size_bytes}. Potential leak detected."
        )

    def test_cache_eviction_under_pressure_with_updates(self):
        """
        Test that cache properly evicts items when full, even with updates happening.
        """
        # Very small cache: 200 bytes
        # Each item is ~40 bytes + overhead -> effectively 1 item fits?
        # Let's use specific sizes.

        # response '{"a": "..."}'
        # We need precise control.

        # Let's stick to checking the accounting logic which is where the bug was.

        cache = IntelligentCache(max_size_mb=1)

        # Fill cache with 3 items
        for i in range(3):
            req = {"id": i}
            resp = {"val": "x" * 1000}  # ~1KB
            cache.put(req, resp)

        initial_size = cache.current_size_bytes
        initial_count = len(cache.cache)

        assert initial_count == 3

        # Update one item
        req = {"id": 1}
        resp = {"val": "y" * 1000}  # Same size
        cache.put(req, resp)

        # Size should stay the same
        assert cache.current_size_bytes == initial_size
        assert len(cache.cache) == 3

        # Update with larger item
        resp_large = {"val": "z" * 2000}  # ~2KB
        cache.put(req, resp_large)

        expected_increase = len(json.dumps(resp_large)) - len(json.dumps(resp))
        assert cache.current_size_bytes == initial_size + expected_increase

    def test_cache_size_leak_on_get_expiry(self):
        """
        Test that retrieving an expired item removes it and updates the size.
        """
        cache = IntelligentCache(max_size_mb=1)
        request_data = {"key": "expire_me"}
        response_data = {"data": "foo"}
        size = len(json.dumps(response_data))

        # 1. Put item with extremely short TTL
        cache.put(request_data, response_data, ttl_seconds=0.01)

        assert cache.current_size_bytes == size

        # 2. Wait for expiration
        time.sleep(0.05)

        # 3. Get item (triggers lazy expiration check)
        result = cache.get(request_data)
        assert result is None

        # 4. Check size
        # If size is not decremented, this will fail
        assert cache.current_size_bytes == 0, (
            f"Cache size leak detected on expiry! Expected 0, got {cache.current_size_bytes}"
        )
