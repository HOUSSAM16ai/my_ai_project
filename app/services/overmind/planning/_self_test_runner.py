# app/overmind/planning/_self_test_runner.py
"""
Self-test execution logic extracted from base_planner for reduced complexity.
Handles timeout-based test execution with quarantine management.
"""

from __future__ import annotations

import inspect
import logging
import threading
from dataclasses import dataclass
from typing import Any

from ._configs import SelfTestConfig

logger = logging.getLogger(__name__)


@dataclass
class SelfTestResult:
    """Result of self-test execution."""

    passed: bool | None  # None = no test method
    error: Exception | None = None
    timed_out: bool = False


def resolve_test_method(planner_cls: type) -> callable | None:
    """
    Resolve the self_test method from planner class.

    Args:
        planner_cls: Planner class to inspect

    Returns:
        Callable test method or None if not found
    """
    test_method = getattr(planner_cls, "self_test", None)
    if not callable(test_method):
        return None
    return test_method


def execute_with_timeout(
    test_method: callable, planner_cls: type, timeout: float
) -> SelfTestResult:
    """
    Execute test method with timeout protection.

    Args:
        test_method: Test method to execute
        planner_cls: Planner class for instance creation if needed
        timeout: Timeout in seconds

    Returns:
        SelfTestResult with execution outcome
    """
    result: dict[str, Any] = {}

    def runner():
        try:
            sig = inspect.signature(test_method)
            # Support @staticmethod / @classmethod / instance method
            if isinstance(test_method, (classmethod, staticmethod)):
                test_method()  # type: ignore
            elif len(sig.parameters) == 0:
                test_method()
            else:
                instance = planner_cls()
                test_method(instance)
            result["ok"] = True
        except Exception as e:
            result["error"] = e

    th = threading.Thread(target=runner, daemon=True)
    th.start()
    th.join(timeout)

    if th.is_alive():
        return SelfTestResult(passed=False, timed_out=True)

    if "error" in result:
        return SelfTestResult(passed=False, error=result["error"])

    return SelfTestResult(passed=True)


def update_quarantine_state(
    state: Any,  # _ReliabilityState
    test_result: SelfTestResult,
    planner_cls: type,
    key: str,
    env: str,
    config: SelfTestConfig,
) -> None:
    """
    Update planner quarantine state based on test result.

    Args:
        state: Reliability state object to update
        test_result: Result of self-test execution
        planner_cls: Planner class being tested
        key: Planner registration key
        env: Environment (prod/dev)
        config: Self-test configuration
    """
    production_ready = getattr(planner_cls, "production_ready", False)

    if test_result.passed is None:
        # No test method
        if production_ready or config.disable_quarantine:
            state.quarantined = False
            state.self_test_passed = True
        else:
            state.self_test_passed = None
        return

    if test_result.timed_out:
        logger.error(f"Planner '{key}' self-test timeout (>{config.timeout_seconds}s).")
        state.self_test_passed = False
        if not config.disable_quarantine:
            state.quarantined = True
        return

    if not test_result.passed:
        logger.error(f"Planner '{key}' self-test FAILED: {test_result.error}")
        state.self_test_passed = False
        if not config.disable_quarantine:
            state.quarantined = True
        else:
            logger.warning(f"Quarantine disabled; allowing planner '{key}' after failed self-test.")
    else:
        state.self_test_passed = True
        if production_ready or env != "prod" or config.disable_quarantine:
            state.quarantined = False
        logger.info(f"Planner '{key}' self-test PASSED (quarantine={state.quarantined}).")


def run_self_test(
    planner_cls: type,
    key: str,
    state: Any,  # _ReliabilityState
    env: str,
    config: SelfTestConfig,
) -> None:
    """
    Main orchestrator for self-test execution.

    Args:
        planner_cls: Planner class to test
        key: Planner registration key
        state: Reliability state to update
        env: Environment (prod/dev)
        config: Self-test configuration
    """
    test_method = resolve_test_method(planner_cls)

    if test_method is None:
        update_quarantine_state(state, SelfTestResult(passed=None), planner_cls, key, env, config)
        return

    logger.debug(f"Running self-test for planner '{key}'...")
    test_result = execute_with_timeout(test_method, planner_cls, config.timeout_seconds)
    update_quarantine_state(state, test_result, planner_cls, key, env, config)
