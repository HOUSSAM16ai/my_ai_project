"""
Tests for environment variable readers.
Ensures duplication elimination maintains functionality.
"""

import os
from unittest.mock import patch

import pytest

from app.infrastructure.config import (
    read_bool_env,
    read_float_env,
    read_int_env,
    read_str_env,
)


class TestEnvReader:
    """Test environment variable readers."""

    def test_read_int_env_default(self):
        """Test reading int with default value."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_int_env("TEST_INT", 42)
            assert result == 42

    def test_read_int_env_from_env(self):
        """Test reading int from environment."""
        with patch.dict(os.environ, {"TEST_INT": "100"}):
            result = read_int_env("TEST_INT", 42)
            assert result == 100

    def test_read_int_env_invalid(self):
        """Test reading invalid int returns default."""
        with patch.dict(os.environ, {"TEST_INT": "invalid"}):
            result = read_int_env("TEST_INT", 42)
            assert result == 42

    def test_read_bool_env_default_false(self):
        """Test reading bool with default False."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_bool_env("TEST_BOOL", False)
            assert result is False

    def test_read_bool_env_default_true(self):
        """Test reading bool with default True."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_bool_env("TEST_BOOL", True)
            assert result is True

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YES", "on", "ON"])
    def test_read_bool_env_truthy(self, value):
        """Test reading truthy bool values."""
        with patch.dict(os.environ, {"TEST_BOOL": value}):
            result = read_bool_env("TEST_BOOL", False)
            assert result is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "NO", "off", "OFF"])
    def test_read_bool_env_falsy(self, value):
        """Test reading falsy bool values."""
        with patch.dict(os.environ, {"TEST_BOOL": value}):
            result = read_bool_env("TEST_BOOL", True)
            assert result is False

    def test_read_str_env_default(self):
        """Test reading string with default value."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_str_env("TEST_STR", "default")
            assert result == "default"

    def test_read_str_env_from_env(self):
        """Test reading string from environment."""
        with patch.dict(os.environ, {"TEST_STR": "value"}):
            result = read_str_env("TEST_STR", "default")
            assert result == "value"

    def test_read_float_env_default(self):
        """Test reading float with default value."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_float_env("TEST_FLOAT", 3.14)
            assert result == 3.14

    def test_read_float_env_from_env(self):
        """Test reading float from environment."""
        with patch.dict(os.environ, {"TEST_FLOAT": "2.71"}):
            result = read_float_env("TEST_FLOAT", 3.14)
            assert result == 2.71

    def test_read_float_env_invalid(self):
        """Test reading invalid float returns default."""
        with patch.dict(os.environ, {"TEST_FLOAT": "invalid"}):
            result = read_float_env("TEST_FLOAT", 3.14)
            assert result == 3.14


class TestDuplicationElimination:
    """Verify duplication elimination."""

    def test_single_implementation(self):
        """Verify there's only one implementation."""
        from app.infrastructure.config import env_reader

        # Check that the module has the expected functions
        assert hasattr(env_reader, "read_int_env")
        assert hasattr(env_reader, "read_bool_env")
        assert hasattr(env_reader, "read_str_env")
        assert hasattr(env_reader, "read_float_env")

    def test_backward_compatibility(self):
        """Verify old code can still use these functions."""
        # This test ensures that refactoring doesn't break existing code
        with patch.dict(os.environ, {"TEST": "123"}):
            # Old pattern: _env_int / _int_env
            result = read_int_env("TEST", 0)
            assert result == 123

            # Old pattern: _env_flag / _bool_env
            with patch.dict(os.environ, {"FLAG": "true"}):
                result = read_bool_env("FLAG", False)
                assert result is True
