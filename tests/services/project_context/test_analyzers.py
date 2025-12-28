"""
Tests for Project Context Analyzers.
"""


import pytest

from app.services.project_context.application.analyzers.issues import IssueAnalyzer
from app.services.project_context.application.analyzers.stats import CodeStatsAnalyzer
from app.services.project_context.application.analyzers.structure import StructureAnalyzer


@pytest.fixture
def project_root(tmp_path):
    """Create a fake project structure."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    # Python file
    (app_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")

    # Subdir with Python file
    services_dir = app_dir / "services"
    services_dir.mkdir()
    (services_dir / "service.py").write_text("def test():\n    pass\n", encoding="utf-8")

    # Hidden file (should be ignored)
    (app_dir / "__init__.py").write_text("", encoding="utf-8")

    # Tests dir
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main():\n    pass\n", encoding="utf-8")

    return tmp_path

def test_code_stats_analyzer(project_root):
    """Test statistics calculation."""
    analyzer = CodeStatsAnalyzer(project_root)
    stats = analyzer.analyze()

    # app/main.py, app/services/service.py, app/__init__.py (skipped if starts with __ check? wait logic check)
    # The logic was: `if "__pycache__" not in str(py_file):`
    # It does NOT skip __init__.py unless explicitly handled.
    # Let's check logic:
    # `for py_file in app_dir.rglob("*.py"): if "__pycache__" ...`
    # So __init__.py is counted.

    # app: main.py(1), services/service.py(2), __init__.py(0 or 1)
    # 3 python files in app.
    # tests: test_main.py (1)

    assert stats.python_files >= 2
    assert stats.test_files == 1
    assert stats.app_lines > 0

def test_structure_analyzer(project_root):
    """Test structure analysis."""
    analyzer = StructureAnalyzer(project_root)
    structure = analyzer.analyze()

    # Should see 'services' directory in app
    service_dir_found = False
    for d in structure.directories:
        if d['name'] == 'services':
            service_dir_found = True
            assert d['file_count'] == 1 # service.py

    assert service_dir_found

def test_issue_analyzer(project_root):
    """Test issue detection."""
    # Create a file with issues
    bad_file = project_root / "app" / "bad.py"
    bad_file.write_text("import os\nprint('debug')\n", encoding="utf-8")

    analyzer = IssueAnalyzer(project_root)
    issues = analyzer.deep_search_issues()

    # Should find print statement
    found_print = False
    for issue in issues['style_issues']:
        if issue['type'] == 'print_statement':
            found_print = True

    assert found_print
