"""مساعدات بناء بنية المشروع لمعرفة Overmind."""

import os
from pathlib import Path


def build_project_structure(project_root: Path) -> dict[str, object]:
    """يبني ملخصاً لبنية المشروع اعتماداً على مسار الجذر."""
    app_dir = project_root / "app"

    structure: dict[str, object] = {
        "root": str(project_root),
        "python_files": 0,
        "directories": 0,
        "main_modules": [],
    }

    for root, dirs, files in os.walk(app_dir):
        structure["directories"] = int(structure["directories"]) + len(dirs)
        for file in files:
            if file.endswith(".py"):
                structure["python_files"] = int(structure["python_files"]) + 1

    if app_dir.exists():
        structure["main_modules"] = [
            d.name for d in app_dir.iterdir()
            if d.is_dir() and not d.name.startswith("__")
        ]

    return structure
