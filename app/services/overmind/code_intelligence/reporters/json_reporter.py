import json
from dataclasses import asdict
from pathlib import Path

from app.services.overmind.code_intelligence.models import ProjectAnalysis


def save_json_report(analysis: ProjectAnalysis, output_path: Path) -> None:
    """Save report as JSON"""
    data = asdict(analysis)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON report saved: {output_path}")
