import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from app.services.overmind.code_intelligence.core import StructuralCodeIntelligence

class TestStructuralCodeIntelligence:

    @pytest.fixture
    def analyzer(self, tmp_path):
        # Patch dependencies that require external environment (Git)
        with patch('app.services.overmind.code_intelligence.core.GitAnalyzer') as MockGit, \
             patch('app.services.overmind.code_intelligence.core.StructuralSmellDetector') as MockSmell:

            mock_git_instance = MockGit.return_value
            mock_git_instance.analyze_file_history.return_value = {
                "total_commits": 10,
                "commits_last_6months": 5,
                "commits_last_12months": 8,
                "num_authors": 2,
                "bugfix_commits": 1,
                "branches_modified": 1
            }

            mock_smell_instance = MockSmell.return_value
            mock_smell_instance.detect_smells.return_value = {
                "is_god_class": False,
                "has_layer_mixing": False,
                "has_cross_layer_imports": False
            }

            # Initialize with temp path and target "."
            return StructuralCodeIntelligence(tmp_path, ["."])

    def test_should_analyze(self, analyzer, tmp_path):
        assert analyzer.should_analyze(tmp_path / "test.py") is True
        assert analyzer.should_analyze(tmp_path / "test.txt") is False
        assert analyzer.should_analyze(tmp_path / "venv/test.py") is False

    def test_analyze_file_simple(self, analyzer, tmp_path):
        test_file = tmp_path / "simple.py"
        test_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        metrics = analyzer.analyze_file(test_file)

        assert metrics is not None
        assert metrics.total_lines == 2
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
