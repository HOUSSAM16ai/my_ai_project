import pytest
import subprocess
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from app.services.agent_tools.domain.metrics import (
    get_project_metrics_handler,
    count_files_handler,
    ProjectMetricsTool,
    FileCountTool
)
from app.services.agent_tools.domain.context import (
    context_awareness_handler,
    ContextAwarenessTool
)

@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock

@pytest.fixture
def mock_os_walk():
    with patch("os.walk") as mock:
        yield mock

@pytest.mark.asyncio
async def test_count_files_handler_git(mock_subprocess_run):
    """Test counting files using git ls-files."""
    mock_subprocess_run.return_value.stdout = "file1.py\nfile2.py\nfile3.txt"
    mock_subprocess_run.return_value.returncode = 0

    # Test all files
    result = await count_files_handler()
    assert result["count"] == 3
    assert result["directory"] == "."

    # Test extension filtering
    result_py = await count_files_handler(extension=".py")
    assert result_py["count"] == 2
    assert result_py["extension"] == ".py"

    # Test directory filtering
    # When directory=".", the handler doesn't filter by startswith, effectively including all files
    result_dir = await count_files_handler(directory=".")
    assert result_dir["count"] == 3

@pytest.mark.asyncio
async def test_count_files_handler_fallback(mock_subprocess_run, mock_os_walk):
    """Test fallback to os.walk when git fails."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["git", "ls-files"])

    # Mock os.walk structure: (root, dirs, files)
    mock_os_walk.return_value = [
        (".", [], ["file1.py", "file2.py", "file3.txt"])
    ]

    result = await count_files_handler()
    assert result["count"] == 3

    # Test extension filtering in fallback
    result_py = await count_files_handler(extension=".py")
    assert result_py["count"] == 2

@pytest.mark.asyncio
async def test_get_project_metrics_handler(mock_subprocess_run):
    """Test retrieving project metrics."""
    mock_subprocess_run.return_value.stdout = "file1.py\nfile2.py\nfile3.txt"
    mock_subprocess_run.return_value.returncode = 0

    with patch("pathlib.Path.read_text", return_value="# Metrics"):
        with patch("pathlib.Path.exists", return_value=True):
            metrics = await get_project_metrics_handler()

            assert metrics["source"] == "PROJECT_METRICS.md"
            assert metrics["content"] == "# Metrics"
            assert metrics["live_stats"]["python_files"] == 2
            assert metrics["live_stats"]["total_files"] == 3

@pytest.mark.asyncio
async def test_context_awareness_handler():
    """Test context awareness extraction."""
    # Test with direct kwargs (legacy)
    result = await context_awareness_handler(active_file="main.py", cursor_line=10)
    assert result["active_file"] == "main.py"
    assert result["cursor_line"] == 10

    # Test with metadata dict
    metadata = {"active_file": "test.py", "cursor_line": 5, "selection": "code"}
    result_meta = await context_awareness_handler(metadata=metadata)
    assert result_meta["active_file"] == "test.py"
    assert result_meta["cursor_line"] == 5
    assert result_meta["selection"] == "code"

    # Test missing context
    result_empty = await context_awareness_handler()
    assert "error" in result_empty

@pytest.mark.asyncio
async def test_tool_classes():
    """Verify tool classes are correctly initialized."""
    metrics_tool = ProjectMetricsTool()
    assert metrics_tool.name == "get_project_metrics"

    file_count_tool = FileCountTool()
    assert file_count_tool.name == "count_files"

    context_tool = ContextAwarenessTool()
    assert context_tool.name == "get_active_context"
