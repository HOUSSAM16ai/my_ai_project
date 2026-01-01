"""
Tests for CS61 Memory Manager | اختبارات مدير الذاكرة
=====================================================

Complete test coverage for cs61_memory module.
هدف: تغطية اختبارات 100%
"""
import gc
import pytest
from app.core.cs61_memory import (
    BoundedList,
    BoundedDict,
    ObjectPool,
    MemoryTracker,
    force_garbage_collection,
    get_object_count_by_type,
)


# ==============================================================================
# Test BoundedList
# ==============================================================================

class TestBoundedList:
    """اختبارات القائمة المحدودة"""
    
    def test_initialization(self):
        """Test BoundedList initialization."""
        blist = BoundedList[int](maxlen=10)
        
        assert len(blist) == 0
        assert blist.maxlen == 10
        assert not blist.is_full
    
    def test_initialization_invalid_maxlen(self):
        """Test invalid maxlen raises error."""
        with pytest.raises(ValueError, match="maxlen must be positive"):
            BoundedList[int](maxlen=0)
        
        with pytest.raises(ValueError):
            BoundedList[int](maxlen=-1)
    
    def test_append_basic(self):
        """Test basic append operation."""
        blist = BoundedList[str](maxlen=3)
        
        blist.append("a")
        blist.append("b")
        
        assert len(blist) == 2
        assert blist[0] == "a"
        assert blist[1] == "b"
    
    def test_append_with_eviction(self):
        """Test automatic eviction when full."""
        blist = BoundedList[int](maxlen=3)
        
        blist.append(1)
        blist.append(2)
        blist.append(3)
        assert blist.is_full
        
        # Adding 4th item should evict first
        blist.append(4)
        
        assert len(blist) == 3
        assert blist[0] == 2
        assert blist[1] == 3
        assert blist[2] == 4
    
    def test_extend(self):
        """Test extend operation."""
        blist = BoundedList[int](maxlen=5)
        
        blist.extend([1, 2, 3])
        assert len(blist) == 3
        
        blist.extend([4, 5, 6])
        # Should keep only last 5
        assert len(blist) == 5
        assert list(blist) == [2, 3, 4, 5, 6]
    
    def test_iteration(self):
        """Test iterating over list."""
        blist = BoundedList[int](maxlen=5)
        blist.extend([1, 2, 3, 4, 5])
        
        items = list(blist)
        assert items == [1, 2, 3, 4, 5]
        
        # Test iter
        for i, item in enumerate(blist, 1):
            assert item == i
    
    def test_getitem(self):
        """Test indexing."""
        blist = BoundedList[str](maxlen=5)
        blist.extend(['a', 'b', 'c'])
        
        assert blist[0] == 'a'
        assert blist[1] == 'b'
        assert blist[2] == 'c'
        assert blist[-1] == 'c'
    
    def test_clear(self):
        """Test clearing list."""
        blist = BoundedList[int](maxlen=5)
        blist.extend([1, 2, 3])
        
        assert len(blist) == 3
        
        blist.clear()
        
        assert len(blist) == 0
        assert not blist.is_full
    
    def test_to_list(self):
        """Test converting to regular list."""
        blist = BoundedList[int](maxlen=5)
        blist.extend([1, 2, 3])
        
        regular_list = blist.to_list()
        
        assert isinstance(regular_list, list)
        assert regular_list == [1, 2, 3]


# ==============================================================================
# Test BoundedDict
# ==============================================================================

class TestBoundedDict:
    """اختبارات القاموس المحدود"""
    
    def test_initialization(self):
        """Test BoundedDict initialization."""
        bdict = BoundedDict[str](maxsize=10)
        
        assert len(bdict) == 0
        assert bdict.maxsize == 10
    
    def test_initialization_invalid_maxsize(self):
        """Test invalid maxsize raises error."""
        with pytest.raises(ValueError, match="maxsize must be positive"):
            BoundedDict[str](maxsize=0)
        
        with pytest.raises(ValueError):
            BoundedDict[str](maxsize=-1)
    
    def test_setitem_and_getitem(self):
        """Test setting and getting items."""
        bdict = BoundedDict[int](maxsize=5)
        
        bdict['a'] = 1
        bdict['b'] = 2
        
        assert bdict['a'] == 1
        assert bdict['b'] == 2
        assert len(bdict) == 2
    
    def test_setitem_update_existing(self):
        """Test updating existing key."""
        bdict = BoundedDict[int](maxsize=5)
        
        bdict['a'] = 1
        assert bdict['a'] == 1
        
        bdict['a'] = 10
        assert bdict['a'] == 10
        assert len(bdict) == 1
    
    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        bdict = BoundedDict[int](maxsize=3)
        
        bdict['a'] = 1
        bdict['b'] = 2
        bdict['c'] = 3
        
        # Adding 4th item should evict 'a' (oldest)
        bdict['d'] = 4
        
        assert len(bdict) == 3
        assert 'a' not in bdict
        assert 'b' in bdict
        assert 'c' in bdict
        assert 'd' in bdict
    
    def test_lru_access_updates_order(self):
        """Test that accessing item updates LRU order."""
        bdict = BoundedDict[int](maxsize=3)
        
        bdict['a'] = 1
        bdict['b'] = 2
        bdict['c'] = 3
        
        # Access 'a' to make it most recently used
        _ = bdict['a']
        
        # Adding 'd' should evict 'b' (now oldest)
        bdict['d'] = 4
        
        assert 'a' in bdict  # Still there
        assert 'b' not in bdict  # Evicted
        assert 'c' in bdict
        assert 'd' in bdict
    
    def test_get_with_default(self):
        """Test get method with default value."""
        bdict = BoundedDict[int](maxsize=5)
        bdict['a'] = 1
        
        assert bdict.get('a') == 1
        assert bdict.get('b') is None
        assert bdict.get('b', 999) == 999
    
    def test_contains(self):
        """Test membership testing."""
        bdict = BoundedDict[int](maxsize=5)
        bdict['a'] = 1
        
        assert 'a' in bdict
        assert 'b' not in bdict
    
    def test_clear(self):
        """Test clearing dict."""
        bdict = BoundedDict[int](maxsize=5)
        bdict['a'] = 1
        bdict['b'] = 2
        
        assert len(bdict) == 2
        
        bdict.clear()
        
        assert len(bdict) == 0
        assert 'a' not in bdict


# ==============================================================================
# Test ObjectPool
# ==============================================================================

class TestObjectPool:
    """اختبارات مُجمِّع الكائنات"""
    
    def test_initialization(self):
        """Test ObjectPool initialization."""
        counter = {'value': 0}
        
        def factory():
            counter['value'] += 1
            return f"object_{counter['value']}"
        
        pool = ObjectPool(factory=factory, size=3)
        
        assert len(pool) == 0
        assert pool.in_use_count == 0
    
    def test_acquire_creates_new_object(self):
        """Test acquiring creates new object when pool empty."""
        counter = {'value': 0}
        
        def factory():
            counter['value'] += 1
            return f"object_{counter['value']}"
        
        pool = ObjectPool(factory=factory, size=3)
        
        with pool.acquire() as obj:
            assert obj == "object_1"
            assert pool.in_use_count == 1
        
        assert pool.in_use_count == 0
        assert len(pool) == 1  # Returned to pool
    
    def test_acquire_reuses_pooled_object(self):
        """Test acquiring reuses objects from pool."""
        counter = {'value': 0}
        
        def factory():
            counter['value'] += 1
            return f"object_{counter['value']}"
        
        pool = ObjectPool(factory=factory, size=3)
        
        # First acquisition
        with pool.acquire() as obj1:
            first_obj = obj1
        
        # Second acquisition should reuse
        with pool.acquire() as obj2:
            assert obj2 == first_obj
            assert counter['value'] == 1  # Only created once
    
    def test_acquire_respects_pool_size(self):
        """Test pool size limit."""
        def factory():
            return "object"
        
        pool = ObjectPool(factory=factory, size=2)
        
        # Acquire 2 objects (max)
        with pool.acquire() as obj1:
            with pool.acquire() as obj2:
                # Try to acquire 3rd (should fail)
                with pytest.raises(RuntimeError, match="Pool exhausted"):
                    with pool.acquire() as obj3:
                        pass
    
    def test_multiple_concurrent_acquisitions(self):
        """Test multiple objects can be acquired."""
        counter = {'value': 0}
        
        def factory():
            counter['value'] += 1
            return counter['value']
        
        pool = ObjectPool(factory=factory, size=3)
        
        with pool.acquire() as obj1:
            assert obj1 == 1
            with pool.acquire() as obj2:
                assert obj2 == 2
                assert pool.in_use_count == 2
        
        assert pool.in_use_count == 0
        assert len(pool) == 2


# ==============================================================================
# Test MemoryTracker
# ==============================================================================

class TestMemoryTracker:
    """اختبارات متتبع الذاكرة"""
    
    def test_initialization(self):
        """Test MemoryTracker initialization."""
        tracker = MemoryTracker()
        assert tracker.get_alive_count('test') == 0
    
    def test_track_object(self):
        """Test tracking objects."""
        tracker = MemoryTracker()
        
        class TestObj:
            def __init__(self, data):
                self.data = data
        
        obj = TestObj('test')
        tracker.track(obj, 'test_objects')
        
        assert tracker.get_alive_count('test_objects') == 1
    
    def test_track_multiple_objects(self):
        """Test tracking multiple objects."""
        tracker = MemoryTracker()
        
        class TestObj:
            def __init__(self, id):
                self.id = id
        
        obj1 = TestObj(1)
        obj2 = TestObj(2)
        
        tracker.track(obj1, 'objects')
        tracker.track(obj2, 'objects')
        
        assert tracker.get_alive_count('objects') == 2
    
    def test_track_with_garbage_collection(self):
        """Test tracking detects garbage collected objects."""
        tracker = MemoryTracker()
        
        class TempObj:
            def __init__(self):
                self.data = 'temp'
        
        # Create and track object
        obj = TempObj()
        tracker.track(obj, 'temp_objects')
        
        assert tracker.get_alive_count('temp_objects') == 1
        
        # Delete and garbage collect
        del obj
        gc.collect()
        
        # Should be 0 now
        assert tracker.get_alive_count('temp_objects') == 0
    
    def test_track_different_categories(self):
        """Test tracking different categories."""
        tracker = MemoryTracker()
        
        class ObjA:
            type = 'A'
        
        class ObjB:
            type = 'B'
        
        obj1 = ObjA()
        obj2 = ObjB()
        
        tracker.track(obj1, 'category_a')
        tracker.track(obj2, 'category_b')
        
        assert tracker.get_alive_count('category_a') == 1
        assert tracker.get_alive_count('category_b') == 1
    
    def test_print_report(self, capsys):
        """Test printing memory report."""
        tracker = MemoryTracker()
        
        class TestObj:
            def __init__(self, id):
                self.id = id
        
        obj1 = TestObj(1)
        obj2 = TestObj(2)
        
        tracker.track(obj1, 'test_objects')
        tracker.track(obj2, 'test_objects')
        
        tracker.print_report()
        
        captured = capsys.readouterr()
        assert "MEMORY LEAK REPORT" in captured.out
        assert "test_objects" in captured.out
        assert "Tracked: 2" in captured.out
    
    def test_cleanup_dead_references(self):
        """Test cleaning up dead references."""
        tracker = MemoryTracker()
        
        class TempObj:
            def __init__(self, id):
                self.id = id
        
        # Track temporary objects
        for i in range(10):
            obj = TempObj(i)
            tracker.track(obj, 'temp')
            # obj goes out of scope immediately
        
        gc.collect()
        gc.collect()  # Double collect to ensure cleanup
        
        # All should be dead or mostly dead
        alive_before_cleanup = tracker.get_alive_count('temp')
        assert alive_before_cleanup <= 2  # Allow some tolerance
        
        # Cleanup
        tracker.cleanup()
        
        # Should still work
        assert tracker.get_alive_count('temp') <= alive_before_cleanup


# ==============================================================================
# Test Memory Utilities
# ==============================================================================

class TestMemoryUtilities:
    """اختبارات أدوات الذاكرة"""
    
    def test_force_garbage_collection(self):
        """Test forced garbage collection."""
        result = force_garbage_collection()
        
        assert isinstance(result, dict)
        assert 'gen0' in result
        assert 'gen1' in result
        assert 'gen2' in result
        
        # All values should be non-negative integers
        assert isinstance(result['gen0'], int)
        assert isinstance(result['gen1'], int)
        assert isinstance(result['gen2'], int)
        assert result['gen0'] >= 0
        assert result['gen1'] >= 0
        assert result['gen2'] >= 0
    
    def test_get_object_count_by_type(self):
        """Test getting object counts by type."""
        result = get_object_count_by_type()
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Should have common types
        assert any('dict' in k or 'list' in k or 'str' in k for k in result.keys())
        
        # All counts should be positive
        for count in result.values():
            assert count > 0


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """اختبارات التكامل"""
    
    def test_bounded_collections_together(self):
        """Test using multiple bounded collections."""
        blist = BoundedList[int](maxlen=100)
        bdict = BoundedDict[str](maxsize=50)
        
        # Fill them up
        for i in range(200):
            blist.append(i)
            bdict[f'key_{i}'] = f'value_{i}'
        
        # Should be bounded
        assert len(blist) == 100
        assert len(bdict) == 50
        
        # Should have latest items
        assert 199 in blist
        assert 'key_199' in bdict
    
    def test_object_pool_with_memory_tracker(self):
        """Test object pool with memory tracking."""
        tracker = MemoryTracker()
        counter = {'value': 0}
        
        class PoolObj:
            def __init__(self, id):
                self.id = id
        
        def factory():
            counter['value'] += 1
            obj = PoolObj(counter['value'])
            tracker.track(obj, 'pool_objects')
            return obj
        
        pool = ObjectPool(factory=factory, size=5)
        
        # Use pool
        with pool.acquire() as obj1:
            assert tracker.get_alive_count('pool_objects') >= 1
        
        with pool.acquire() as obj2:
            assert tracker.get_alive_count('pool_objects') >= 1
    
    def test_memory_leak_detection_workflow(self):
        """Test complete memory leak detection workflow."""
        tracker = MemoryTracker()
        
        class DataObj:
            def __init__(self, id):
                self.id = id
                self.data = 'x' * 1000
        
        # Simulate creating objects (some leak, some cleaned)
        persistent_objects = []
        
        for i in range(100):
            obj = DataObj(i)
            tracker.track(obj, 'all_objects')
            
            # Keep some objects (simulating leak)
            if i % 10 == 0:
                persistent_objects.append(obj)
        
        gc.collect()
        
        # Should have ~10 alive (10% leak rate)
        alive_count = tracker.get_alive_count('all_objects')
        assert 8 <= alive_count <= 12  # Some tolerance
        
        # Cleanup tracked references
        tracker.cleanup()
        
        # Clear persistent objects
        persistent_objects.clear()
        gc.collect()
        
        # Should be close to 0 now
        assert tracker.get_alive_count('all_objects') <= 2


# ==============================================================================
# Edge Cases
# ==============================================================================

class TestEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_bounded_list_maxlen_one(self):
        """Test BoundedList with maxlen=1."""
        blist = BoundedList[str](maxlen=1)
        
        blist.append('a')
        assert len(blist) == 1
        
        blist.append('b')
        assert len(blist) == 1
        assert blist[0] == 'b'
    
    def test_bounded_dict_maxsize_one(self):
        """Test BoundedDict with maxsize=1."""
        bdict = BoundedDict[int](maxsize=1)
        
        bdict['a'] = 1
        assert len(bdict) == 1
        
        bdict['b'] = 2
        assert len(bdict) == 1
        assert 'a' not in bdict
        assert 'b' in bdict
    
    def test_object_pool_size_one(self):
        """Test ObjectPool with size=1."""
        def factory():
            return "single_object"
        
        pool = ObjectPool(factory=factory, size=1)
        
        with pool.acquire() as obj:
            assert obj == "single_object"
            
            # Can't acquire another
            with pytest.raises(RuntimeError):
                with pool.acquire() as obj2:
                    pass
    
    def test_memory_tracker_empty_category(self):
        """Test getting count for non-existent category."""
        tracker = MemoryTracker()
        
        count = tracker.get_alive_count('non_existent')
        assert count == 0
    
    def test_bounded_list_large_maxlen(self):
        """Test BoundedList with very large maxlen."""
        blist = BoundedList[int](maxlen=1000000)
        
        # Add many items (but less than maxlen)
        for i in range(10000):
            blist.append(i)
        
        assert len(blist) == 10000
        assert not blist.is_full
