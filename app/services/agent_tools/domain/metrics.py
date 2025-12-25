"""
Domain tools for project metrics and file system statistics.
"""
import os
import subprocess
from pathlib import Path
from typing import Any

from app.services.agent_tools.refactored.tool import Tool, ToolConfig


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(os.getcwd())

async def count_files_handler(directory: str = ".", extension: str | None = None) -> dict[str, Any]:
    """
    Count files in a directory, optionally filtering by extension.
    Respects .gitignore if possible (using git ls-files if available).
    """
    try:
        cmd = ["git", "ls-files"]

        # Note: git ls-files lists all files.
        # Filtering by directory is post-processing or strict argument.

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = result.stdout.splitlines()

        if extension:
            files = [f for f in files if f.endswith(extension)]

        if directory != ".":
             files = [f for f in files if f.startswith(directory)]

        count = len(files)
    except subprocess.CalledProcessError:
        # Fallback to os.walk
        count = 0
        root_path = get_project_root() / directory
        for _, _, filenames in os.walk(root_path):
            for f in filenames:
                if extension and not f.endswith(extension):
                    continue
                count += 1

    return {"directory": directory, "extension": extension, "count": count}

async def get_project_metrics_handler() -> dict[str, Any]:
    """Read PROJECT_METRICS.md and supplement with live data."""
    metrics = {}
    metrics_file = get_project_root() / "PROJECT_METRICS.md"

    if metrics_file.exists():
        content = metrics_file.read_text()
        metrics["source"] = "PROJECT_METRICS.md"
        metrics["content"] = content
    else:
        metrics["source"] = "calculated"
        metrics["content"] = "Metrics file not found."

    # Live stats
    # We call the handler directly or replicate logic.
    # Replicating logic is safer to avoid circular async issues if simple.
    # But we can await the handler.
    py_count = (await count_files_handler(".", ".py"))["count"]
    total_count = (await count_files_handler("."))["count"]

    metrics["live_stats"] = {
        "python_files": py_count,
        "total_files": total_count,
    }
    return metrics

class ProjectMetricsTool(Tool):
    """Tool to retrieve project metrics."""

    def __init__(self):
        config = ToolConfig(
            name="get_project_metrics",
            description="Retrieves project metrics including test coverage and file counts.",
            category="metrics",
            capabilities=["read_file", "shell_exec"],
            aliases=["metrics", "stats"],
            handler=get_project_metrics_handler
        )
        super().__init__(config)

class FileCountTool(Tool):
    """Tool to count files."""

    def __init__(self):
        config = ToolConfig(
            name="count_files",
            description="Counts files in the project or a directory.",
            category="fs",
            aliases=["file_count"],
            handler=count_files_handler
        )
        super().__init__(config)
