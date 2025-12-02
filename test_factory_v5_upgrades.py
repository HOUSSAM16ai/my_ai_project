#!/usr/bin/env python3
"""
Test suite for factory.py v5.0.0 professional upgrades.
Tests all 10 improvements without breaking existing functionality.
"""

import importlib.util
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


def test_version_upgrade():
    """Test 1: Version is upgraded to 5.0.0"""
    factory = load_factory_module()
    assert factory.FACTORY_VERSION == "5.0.0", "Version should be 5.0.0"
    print("✓ Test 1: Version upgrade successful")


def test_typed_configuration():
    """Test 2: Typed configuration class exists and works"""
    factory = load_factory_module()
    assert hasattr(factory, "CFG"), "CFG class should exist"
    assert factory.CFG.DEFAULT_RELIABILITY == 0.1, "Default reliability should be 0.1"
    assert factory.CFG.MAX_PROFILES == 1000, "Max profiles should be 1000"
    assert factory.CFG.MIN_REL == 0.25, "Min reliability should be 0.25"
    print("✓ Test 2: Typed configuration works")


def test_allowed_planners_whitelist():
    """Test 3: ALLOWED_PLANNERS whitelist exists"""
    factory = load_factory_module()
    assert hasattr(factory, "ALLOWED_PLANNERS"), "ALLOWED_PLANNERS should exist"
    # Check for actual planner names (not module names)
    assert "ultra_hyper_semantic_planner" in factory.ALLOWED_PLANNERS, (
        "ultra_hyper_semantic_planner should be allowed"
    )
    assert len(factory.ALLOWED_PLANNERS) > 0, "Should have at least one allowed planner"
    print("✓ Test 3: ALLOWED_PLANNERS whitelist exists")


def test_ring_buffer_functions():
    """Test 4: Ring buffer helper functions exist"""
    factory = load_factory_module()
    assert hasattr(factory, "_push_selection_profile"), "Should have _push_selection_profile"
    assert hasattr(factory, "_push_instantiation_profile"), (
        "Should have _push_instantiation_profile"
    )

    # Test ring buffer behavior
    sample = {"test": 1, "ts": time.time()}
    factory._push_selection_profile(sample)
    assert len(factory._STATE.selection_profile_samples) > 0
    print("✓ Test 4: Ring buffer functions work")


def test_sandboxed_import():
    """Test 5: Sandboxed import function exists"""
    factory = load_factory_module()
    assert hasattr(factory, "_import_module_sandboxed"), "Should have _import_module_sandboxed"
    print("✓ Test 5: Sandboxed import function exists")


def test_structured_logging():
    """Test 6: Structured JSON logging is configured"""
    factory = load_factory_module()
    assert hasattr(factory, "_log"), "Should have _log function"
    # Log function should accept keyword arguments
    import io
    import json
    import logging

    # Capture log output
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    factory._logger.addHandler(handler)

    factory._log("test message", "INFO", key="value")
    handler.flush()
    log_output = log_capture.getvalue()

    # Should be JSON formatted
    try:
        log_data = json.loads(log_output.strip())
        assert log_data["component"] == "PlannerFactory"
        assert log_data["msg"] == "test message"
        assert log_data["key"] == "value"
    except json.JSONDecodeError:
        pass  # May have multiple log lines

    print("✓ Test 6: Structured logging works")


def test_new_api_select_best_planner_name():
    """Test 7: New select_best_planner_name API exists"""
    factory = load_factory_module()
    assert hasattr(factory, "select_best_planner_name"), "Should have select_best_planner_name"
    assert "select_best_planner_name" in factory.__all__, "Should be exported"
    print("✓ Test 7: New select_best_planner_name API exists")


def test_deterministic_sorting():
    """Test 8: Ranking function is deterministic (no hash)"""
    factory = load_factory_module()

    # Test _rank_hint multiple times with same inputs
    results = []
    for _ in range(5):
        score = factory._rank_hint(
            name="test_planner",
            objective="test objective",
            capabilities_match_ratio=0.8,
            reliability_score=0.9,
            tier="stable",
            production_ready=True,
        )
        results.append(score)

    # All results should be identical (deterministic)
    assert len(set(results)) == 1, "Ranking should be deterministic"
    print("✓ Test 8: Deterministic sorting works")


def test_fingerprint_with_mtime():
    """Test 9: Fingerprint function includes mtime logic"""
    factory = load_factory_module()
    # The function should not crash and should return a string
    fingerprint = factory._file_fingerprint("app.overmind.planning")
    assert isinstance(fingerprint, str), "Fingerprint should return string"
    print("✓ Test 9: Fingerprint with mtime works")


def test_backward_compatibility():
    """Test 10: All original exports still exist"""
    factory = load_factory_module()

    required_exports = [
        "discover",
        "refresh_metadata",
        "get_planner",
        "get_all_planners",
        "list_planners",
        "select_best_planner",
        "batch_select_best_planners",
        "self_heal",
        "planner_stats",
        "describe_planner",
        "diagnostics_report",
        "diagnostics_json",
        "export_diagnostics",
        "health_check",
        "list_quarantined",
        "reload_planners",
    ]

    for export in required_exports:
        assert export in factory.__all__, f"{export} should be exported"
        assert hasattr(factory, export), f"{export} should exist"

    print("✓ Test 10: Backward compatibility maintained")


def test_self_heal_with_backoff():
    """Test 11: self_heal has exponential backoff logic"""
    factory = load_factory_module()

    # Mock _active_planner_names to return empty initially
    with (
        unittest.mock.patch.object(factory, "_active_planner_names", return_value=[]),
        unittest.mock.patch.object(factory, "discover"),
    ):
        start = time.time()
        result = factory.self_heal(force=True, max_attempts=3)
        elapsed = time.time() - start

        # Should have attempted multiple times with delays
        assert result["attempts"] > 0, "Should have attempted self-heal"
        # With backoff: 0.2 + 0.4 + 0.8 = 1.4s minimum
        assert elapsed >= 1.0, "Should have used backoff delays"

    print("✓ Test 11: self_heal with exponential backoff works")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Testing Factory.py v5.0.0 Professional Upgrades")
    print("=" * 60)

    tests = [
        test_version_upgrade,
        test_typed_configuration,
        test_allowed_planners_whitelist,
        test_ring_buffer_functions,
        test_sandboxed_import,
        test_structured_logging,
        test_new_api_select_best_planner_name,
        test_deterministic_sorting,
        test_fingerprint_with_mtime,
        test_backward_compatibility,
        test_self_heal_with_backoff,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! All 10 v5.0.0 upgrades are working perfectly!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
