
import pytest
from unittest.mock import patch, mock_open
from app.core.agents.system_principles import (
    get_system_principles,
    get_architecture_system_principles,
    validate_system_principles,
    format_system_principles,
    SystemPrinciple,
    _get_all_system_principles,
    _get_all_architecture_principles,
)

# Sample YAML content for testing
SAMPLE_YAML = """
system_principles:
  - number: 1
    statement: "Test Principle 1"
  - number: 2
    statement: "Test Principle 2"

architecture_principles:
  - number: 1
    statement: "Arch Principle 1"
"""

class TestSystemPrinciplesRefactor:
    """Test suite for the refactored system principles loading mechanism."""

    def setup_method(self):
        # Clear lru_cache to ensure tests run fresh
        _get_all_system_principles.cache_clear()
        _get_all_architecture_principles.cache_clear()

    def test_load_principles_integration(self):
        """Verify that principles are correctly loaded from the actual YAML file."""
        principles = get_system_principles()
        assert len(principles) == 100
        assert principles[0].number == 1
        assert "تعدد الأشكال" in principles[0].statement

        arch_principles = get_architecture_system_principles()
        assert len(arch_principles) == 100
        assert arch_principles[0].number == 1

    def test_validation_logic(self):
        """Verify that validation logic works correctly."""
        # Valid set (subset for testing, normally requires 100)
        # We need to mock the requirement for 100 items if we want to test smaller sets,
        # or we just rely on the main test which checks the full file.

        # Let's test the failure cases with a small manual list
        bad_principles = (
            SystemPrinciple(1, "Ok"),
            SystemPrinciple(1, "Duplicate Number"),
        )

        with pytest.raises(ValueError, match="ترقيم مبادئ النظام يجب أن يغطي النطاق الكامل"):
            validate_system_principles(bad_principles)

    def test_format_output(self):
        """Verify the formatting function."""
        # Mocking the return value of get_system_principles to test formatting
        with patch('app.core.agents.system_principles.get_system_principles') as mock_get:
            mock_get.return_value = (
                SystemPrinciple(1, "Alpha"),
                SystemPrinciple(2, "Beta"),
            )

            output = format_system_principles(header="Test Header", bullet="*")
            assert "Test Header" in output
            assert "* 1. Alpha" in output
            assert "* 2. Beta" in output

    def test_missing_file_handling(self):
        """Verify behavior when config file is missing."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            # Should return empty tuple instead of crashing
            assert get_system_principles() == ()
