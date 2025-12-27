#!/usr/bin/env python3
"""
Update Project Metrics
======================
Runs quality metrics collection and updates PROJECT_METRICS.md.
"""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def main():
    print("🚀 Collecting quality metrics...")

    # Run the quality metrics script
    result = subprocess.run(
        ["python", "scripts/quality_metrics.py", "--json"],
        check=False, capture_output=True,
        text=True
    )

    output = result.stdout
    json_start = output.find('{')

    if json_start == -1:
        print("❌ Failed to find JSON in output")
        print("Stderr:", result.stderr)
        print("Stdout:", result.stdout)
        return

    try:
        data = json.loads(output[json_start:])
    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON: {e}")
        return

    # Extract metrics
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    code = data.get("code", {})
    test = data.get("test", {})
    security = data.get("security", {})
    linting = data.get("linting", {})

    python_files = code.get("python_files", 0)
    lines_of_code = code.get("lines_of_code", 0)

    coverage = test.get("coverage_percent", 0)

    security_total = security.get("security_total", 0)
    security_high = security.get("security_high", 0)

    ruff_violations = linting.get("ruff_violations", 0)
    pylint_score = linting.get("pylint_score", 0.0)

    # Generate Markdown content
    content = f"""# Project Metrics - Single Source of Truth
# Last Updated: {timestamp}

## 🏥 Health Status (الحالة الصحية)
- **Test Coverage**: {coverage}%
- **Security Issues**: {security_total} (High: {security_high})
- **Linter Violations**: {ruff_violations}
- **Pylint Score**: {pylint_score}/10.0

## 📏 Codebase Size (حجم الكود)
- **Total Python Files**: {python_files}
- **Lines of Code**: {lines_of_code}

## ℹ️ Verification
- **Method**: Automated via `scripts/quality_metrics.py`
- **Agent**: Overmind CLI
"""

    # Write to file
    Path("PROJECT_METRICS.md").write_text(content, encoding="utf-8")
    print("✅ PROJECT_METRICS.md updated successfully.")
    print("------------------------------------------------")
    print(content)
    print("------------------------------------------------")

if __name__ == "__main__":
    main()
