"""
Handlers for metadata operations (existence, listing).
"""

import os

from app.services.agent_tools.domain.filesystem.validators.path_validator import validate_path
from app.services.agent_tools.tool_model import ToolResult


def file_exists_logic(path: str) -> ToolResult:
    """Checks file existence and type."""
    try:
        abs_path = validate_path(path, allow_missing=True)
        return ToolResult(
            ok=True,
            data={
                "path": abs_path,
                "exists": os.path.exists(abs_path),
                "is_dir": os.path.isdir(abs_path),
                "is_file": os.path.isfile(abs_path),
            },
        )
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def list_dir_logic(path: str = ".", max_entries: int = 400) -> ToolResult:
    """Lists directory contents."""
    try:
        abs_path = validate_path(path, allow_missing=True)

        if not os.path.isdir(abs_path):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")

        entries = []
        # Sort for deterministic output
        for name in sorted(os.listdir(abs_path))[:max_entries]:
            p = os.path.join(abs_path, name)
            entries.append(
                {
                    "name": name,
                    "is_dir": os.path.isdir(p),
                    "is_file": os.path.isfile(p),
                    "size": os.path.getsize(p) if os.path.isfile(p) else None,
                }
            )

        return ToolResult(ok=True, data={"path": abs_path, "entries": entries})

    except Exception as e:
        return ToolResult(ok=False, error=str(e))
