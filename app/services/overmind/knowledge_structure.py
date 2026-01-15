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

    for _root, dirs, files in os.walk(app_dir):
        structure["directories"] = int(structure["directories"]) + len(dirs)
        for file in files:
            if file.endswith(".py"):
                structure["python_files"] = int(structure["python_files"]) + 1

    if app_dir.exists():
        structure["main_modules"] = [
            d.name for d in app_dir.iterdir() if d.is_dir() and not d.name.startswith("__")
        ]

    return structure


def build_microservices_summary(project_root: Path) -> dict[str, object]:
    """يبني ملخصاً للخدمات المصغرة اعتماداً على مجلد microservices."""
    microservices_dir = project_root / "microservices"
    services: list[str] = []

    if microservices_dir.exists():
        for item in microservices_dir.iterdir():
            if item.is_dir() and (item / "main.py").exists():
                services.append(item.name)

    services.sort()

    return {
        "root": str(microservices_dir),
        "total_services": len(services),
        "services": services,
    }
