# tests/test_template.py
from unittest.mock import AsyncMock

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st

# === Unified Test Template ===
# Use this class as a mixin or base for all test classes to ensure consistency.


class UnifiedTestTemplate:
    """
    Base class enforcing the 'Superhuman' testing standard.
    Includes helpers for async mocking, property-based testing setup, and verification.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Standard setup/teardown for every test."""
        # Setup logic here (e.g., reset singletons)
        yield
        # Teardown logic here (e.g., clear mocks)

    @staticmethod
    def async_mock(return_value=None, side_effect=None):
        """Helper to create an AsyncMock with less boilerplate."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock

    @staticmethod
    def assert_invariants(obj, invariants: dict):
        """
        Check that an object satisfies a set of invariant conditions.
        :param obj: The object to check.
        :param invariants: Dict of {description: check_function(obj) -> bool}
        """
        for desc, check in invariants.items():
            assert check(obj), f"Invariant violated: {desc}"

    # --- Property-Based Testing Helpers ---
    # Standard settings for hypothesis to be thorough but fast enough for CI
    HYPOTHESIS_SETTINGS = settings(
        max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
    )

    # --- Fuzzing Helpers ---
    @staticmethod
    def generate_random_unicode(min_len=0, max_len=1000):
        return st.text(min_size=min_len, max_size=max_len)

    @staticmethod
    def generate_complex_json():
        return st.recursive(
            st.booleans() | st.floats() | st.text(),
            lambda children: st.lists(children) | st.dictionaries(st.text(), children),
            max_leaves=10,
        )
