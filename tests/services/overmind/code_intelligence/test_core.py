import sys
from unittest.mock import MagicMock, patch

# Mock pythonjsonlogger
mock_jsonlogger = MagicMock()
sys.modules["pythonjsonlogger"] = mock_jsonlogger
sys.modules["pythonjsonlogger.jsonlogger"] = mock_jsonlogger

# Mock pydantic
mock_pydantic = MagicMock()
sys.modules["pydantic"] = mock_pydantic
sys.modules["pydantic_settings"] = MagicMock()

import pytest

# We need to make sure pydantic is mocked BEFORE importing core
from app.services.overmind.code_intelligence.core import StructuralCodeIntelligence


class TestStructuralCodeIntelligence:

    @pytest.fixture
    def analyzer(self, tmp_path):
        # Patch dependencies that require external environment (Git)
        with patch('app.services.overmind.code_intelligence.core.GitAnalyzer') as mock_git, \
             patch('app.services.overmind.code_intelligence.core.StructuralSmellDetector') as mock_smell:

            mock_git_instance = mock_git.return_value
            mock_git_instance.analyze_file_history.return_value = {
                "total_commits": 10,
                "commits_last_6months": 5,
                "commits_last_12months": 8,
                "num_authors": 2,
                "bugfix_commits": 1,
                "branches_modified": 1
            }

            mock_smell_instance = mock_smell.return_value
            mock_smell_instance.detect_smells.return_value = {
                "is_god_class": False,
                "has_layer_mixing": False,
                "has_cross_layer_imports": False
            }

            # Initialize with temp path and target "."
            instance = StructuralCodeIntelligence(tmp_path, ["."])
            # Override exclude patterns to avoid excluding tmp_path which might contain "test"
            instance.exclude_patterns = ["__pycache__", ".git", "venv"]
            return instance

    def test_should_analyze(self, analyzer, tmp_path):
        assert analyzer.should_analyze(tmp_path / "valid_code.py") is True
        assert analyzer.should_analyze(tmp_path / "text.txt") is False
        # We removed "venv" from excludes for this test instance specifically?
        # No, we kept "venv".
        assert analyzer.should_analyze(tmp_path / "venv/lib.py") is False

    def test_analyze_file_simple(self, analyzer, tmp_path):
        test_file = tmp_path / "simple.py"
        test_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        metrics = analyzer.analyze_file(test_file)

        assert metrics is not None
        # "def hello():\n    pass\n".split("\n") -> ['def hello():', '    pass', ''] -> 3 lines
        assert metrics.total_lines == 3
        assert metrics.num_functions == 1
        assert metrics.total_commits == 10  # From mock
        assert metrics.is_god_class is False # From mock

    def test_analyze_project(self, analyzer, tmp_path):
        f1 = tmp_path / "f1.py"
        f1.write_text("def a(): pass", encoding="utf-8")
        f2 = tmp_path / "f2.py"
        f2.write_text("class B: pass", encoding="utf-8")

        analysis = analyzer.analyze_project()

        assert analysis.total_files == 2
        assert len(analysis.files) == 2
        # Verify hotspot calculation ran
        assert analysis.files[0].hotspot_score is not None
