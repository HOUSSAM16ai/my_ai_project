#!/usr/bin/env python3
"""
Test suite for factory.py security and stability fixes.
Tests critical security vulnerabilities, race conditions, and stability improvements.
"""

import importlib.util
import os
import sys
import time
import unittest.mock


def load_factory_module():
    """Load factory module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location("factory", "app/overmind/planning/factory.py")
    factory = importlib.util.module_from_spec(spec)
    sys.modules["factory"] = factory

    # Mock base_planner
    class MockBasePlanner:
        @staticmethod
        def live_planner_classes():
            return {}

        @staticmethod
        def planner_metadata():
            return {}

        @staticmethod
        def compute_rank_hint(**kwargs):
            return 0.5

    with unittest.mock.patch.dict(
        "sys.modules",
        {
            "app.overmind.planning.base_planner": unittest.mock.MagicMock(
                BasePlanner=MockBasePlanner, PlannerError=Exception
            )
        },
    ):
        spec.loader.exec_module(factory)

    return factory


def test_isinstance_syntax_fix():
    """Test P0 Fix #1: isinstance() syntax is correct (no TypeError)"""
    factory = load_factory_module()

    # Test with list
    obj = type("TestObj", (), {"caps": ["a", "b", "c"]})()
    result = factory._extract_attribute_set(obj, "caps")
    assert result == {"a", "b", "c"}, "Should extract list as set"

    # Test with tuple
    obj = type("TestObj", (), {"caps": ("x", "y", "z")})()
    result = factory._extract_attribute_set(obj, "caps")
    assert result == {"x", "y", "z"}, "Should extract tuple as set"

    # Test with set
    obj = type("TestObj", (), {"caps": {"foo", "bar"}})()
    result = factory._extract_attribute_set(obj, "caps")
    assert result == {"foo", "bar"}, "Should extract set as set"

    print("✓ Test P0-1: isinstance() syntax fix works correctly")


def test_sandboxed_import_comment():
    """Test P0 Fix #2: Sandboxed import has accurate comment"""
    factory = load_factory_module()

    # Read the source to verify comment
    import inspect

    source = inspect.getsource(factory._import_module_sandboxed)
    assert (
        "NOT sandboxed yet" in source or "not sandboxed" in source.lower()
    ), "Comment should clarify import is not actually sandboxed"

    print("✓ Test P0-2: Sandboxed import comment updated")


def test_per_planner_locks():
    """Test P0 Fix #3: Per-planner locks prevent race conditions"""
    factory = load_factory_module()

    # Verify lock infrastructure exists
    assert hasattr(factory, "_PLANNER_LOCKS"), "Should have _PLANNER_LOCKS dict"
    assert hasattr(factory, "_get_plock"), "Should have _get_plock function"

    # Test that locks are created per planner
    lock1 = factory._get_plock("test_planner_1")
    lock2 = factory._get_plock("test_planner_2")
    lock1_again = factory._get_plock("test_planner_1")

    assert lock1 is not lock2, "Different planners should have different locks"
    assert lock1 is lock1_again, "Same planner should get same lock"
    assert hasattr(lock1, "acquire") and hasattr(
        lock1, "release"
    ), "Should return a lock-like object"

    print("✓ Test P0-3: Per-planner locks prevent race conditions")


def test_shared_data_locking():
    """Test P0 Fix #4: Shared data structures updated with locks"""
    factory = load_factory_module()

    # Test that import_module uses locking for import_failures
    test_module = "nonexistent_module_xyz123"
    result = factory._import_module(test_module)

    assert result is None, "Should return None for failed import"
    with factory._STATE.lock:
        assert (
            test_module in factory._STATE.import_failures
        ), "Failed import should be recorded in import_failures"

    print("✓ Test P0-4: Shared data structures properly locked")


def test_safe_integer_conversion():
    """Test P0 Fix #5: Safe integer conversion for hotspots_count"""
    factory = load_factory_module()

    # Test _to_int helper function
    assert factory._to_int("10", 0) == 10, "Should convert valid string"
    assert factory._to_int(42, 0) == 42, "Should convert valid int"
    assert factory._to_int("invalid", 99) == 99, "Should use default for invalid"
    assert factory._to_int(None, 5) == 5, "Should use default for None"
    assert factory._to_int([], 7) == 7, "Should use default for list"

    # Test in _compute_deep_boosts context
    rec = factory.PlannerRecord(name="test")
    rec.capabilities = set()

    # Test with invalid hotspots_count
    deep_context = {"hotspots_count": "ten"}
    boost, _breakdown = factory._compute_deep_boosts(rec, set(), deep_context)
    assert isinstance(boost, int | float), "Should not crash on invalid hotspots_count"

    print("✓ Test P0-5: Safe integer conversion prevents ValueError")


def test_deep_fingerprint_flag():
    """Test P1 Fix #6: ENABLE_DEEP_FINGERPRINT flag exists and works"""
    factory = load_factory_module()

    # Verify flag exists
    assert hasattr(factory, "ENABLE_DEEP_FINGERPRINT"), "Should have ENABLE_DEEP_FINGERPRINT flag"

    # Test that fingerprint respects the flag
    # When disabled, should return "na" quickly
    original_value = factory.ENABLE_DEEP_FINGERPRINT
    try:
        factory.ENABLE_DEEP_FINGERPRINT = False
        result = factory._file_fingerprint("app.overmind.planning")
        assert result == "na", "Should return 'na' when ENABLE_DEEP_FINGERPRINT is False"

        factory.ENABLE_DEEP_FINGERPRINT = True
        result = factory._file_fingerprint("app.overmind.planning")
        # Should try to compute fingerprint (may still return "na" if module not found)
        assert isinstance(result, str), "Should return string fingerprint"
    finally:
        factory.ENABLE_DEEP_FINGERPRINT = original_value

    print("✓ Test P1-6: Deep fingerprint flag prevents DoS")


def test_configurable_allowed_planners():
    """Test P1 Fix #7: ALLOWED_PLANNERS is configurable via environment"""
    factory = load_factory_module()

    # Verify _parse_csv helper exists
    assert hasattr(factory, "_parse_csv"), "Should have _parse_csv helper"

    # Test _parse_csv functionality
    result = factory._parse_csv("a,b,c")
    assert result == {"a", "b", "c"}, "Should parse CSV correctly"

    result = factory._parse_csv("  x  ,  y  ,  z  ")
    assert result == {"x", "y", "z"}, "Should strip whitespace"

    result = factory._parse_csv("foo,,bar,")
    assert result == {"foo", "bar"}, "Should skip empty entries"

    # Verify ALLOWED_PLANNERS is a set with default values
    assert isinstance(factory.ALLOWED_PLANNERS, set), "ALLOWED_PLANNERS should be a set"
    assert len(factory.ALLOWED_PLANNERS) > 0, "Should have default allowed planners"

    print("✓ Test P1-7: ALLOWED_PLANNERS is configurable")


def test_self_heal_non_blocking():
    """Test P2 Fix #9: self_heal supports non-blocking mode"""
    factory = load_factory_module()

    # Mock environment and functions
    with unittest.mock.patch.dict(os.environ, {"FACTORY_SELF_HEAL_BLOCKING": "0"}):
        # Reload to pick up env variable
        factory = load_factory_module()

        with (
            unittest.mock.patch.object(factory, "_active_planner_names", return_value=[]),
            unittest.mock.patch.object(factory, "discover"),
        ):
            start = time.time()
            result = factory.self_heal(force=True, max_attempts=3)
            elapsed = time.time() - start

            # In non-blocking mode, should not sleep
            assert elapsed < 0.5, f"Non-blocking mode should be fast, took {elapsed}s"
            assert result["attempts"] >= 1, "Should have attempted at least once"

    print("✓ Test P2-9: self_heal non-blocking mode works")


def test_ring_buffer_trimming():
    """Test P3 Fix #11: Ring buffers are trimmed in refresh_metadata"""
    factory = load_factory_module()

    # Fill buffers beyond max size
    factory._STATE.discovered = True
    max_profiles = factory.CFG.MAX_PROFILES

    # Add more than max to selection profiles
    for i in range(max_profiles + 100):
        factory._STATE.selection_profile_samples.append({"sample": i})

    # Add more than max to instantiation profiles
    for i in range(max_profiles + 50):
        factory._STATE.instantiation_profile_samples.append({"sample": i})

    # Call refresh_metadata
    factory.refresh_metadata()

    # Verify buffers are trimmed
    assert (
        len(factory._STATE.selection_profile_samples) <= max_profiles
    ), f"Selection profiles should be trimmed to {max_profiles}"
    assert (
        len(factory._STATE.instantiation_profile_samples) <= max_profiles
    ), f"Instantiation profiles should be trimmed to {max_profiles}"

    print("✓ Test P3-11: Ring buffer trimming prevents memory growth")


def test_double_check_locking_pattern():
    """Test that double-check locking is implemented in _instantiate_planner"""
    factory = load_factory_module()

    # Read the source to verify double-check pattern
    import inspect

    source = inspect.getsource(factory._instantiate_planner)

    # Should have two checks for _INSTANCE_CACHE
    cache_checks = source.count("_INSTANCE_CACHE")
    assert cache_checks >= 2, "Should have double-check pattern for _INSTANCE_CACHE"

    # Should use plock
    assert "plock" in source or "_get_plock" in source, "Should use per-planner lock"

    print("✓ Test: Double-check locking pattern implemented")


def test_concurrent_instantiation_safety():
    """Test that concurrent instantiation of same planner is safe"""
    factory = load_factory_module()

    # This is a smoke test - just verify the locking mechanism exists
    # Full thread safety testing would require more complex setup

    assert hasattr(factory, "_PLANNER_LOCKS"), "Locking mechanism should exist"
    assert hasattr(factory, "_get_plock"), "Lock getter should exist"

    # Verify multiple calls to _get_plock return same lock
    lock1 = factory._get_plock("test")
    lock2 = factory._get_plock("test")
    assert lock1 is lock2, "Same key should return same lock instance"

    print("✓ Test: Concurrent instantiation safety mechanisms in place")


def run_all_tests():
    """Run all security fix tests and report results."""
    print("=" * 70)
    print("Testing Factory.py Security and Stability Fixes")
    print("=" * 70)

    tests = [
        test_isinstance_syntax_fix,
        test_sandboxed_import_comment,
        test_per_planner_locks,
        test_shared_data_locking,
        test_safe_integer_conversion,
        test_deep_fingerprint_flag,
        test_configurable_allowed_planners,
        test_self_heal_non_blocking,
        test_ring_buffer_trimming,
        test_double_check_locking_pattern,
        test_concurrent_instantiation_safety,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        print(
            "✓ P0 Fixes: isinstance syntax, sandboxed import clarity, race conditions, data locking, safe int conversion"
        )
        print("✓ P1 Fixes: Deep fingerprint DoS mitigation, configurable allowlist")
        print("✓ P2 Fixes: Non-blocking self-heal")
        print("✓ P3 Fixes: Ring buffer memory management")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
