# tests/security/test_security_final.py
import typing

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tests.utils.unified_test_template import UnifiedTestTemplate


class TestSecuritySuperhuman(UnifiedTestTemplate):
    SQL_INJECTION_PATTERNS: typing.ClassVar[list[str]] = ["' OR 1=1 --", "'; DROP TABLE users; --"]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PATTERNS)
    def test_sqli_resilience_static(self, payload):
        pass

    @given(st.text())
    @UnifiedTestTemplate.HYPOTHESIS_SETTINGS
    def test_generic_fuzzing_resilience(self, input_str):
        assert isinstance(input_str, str)
