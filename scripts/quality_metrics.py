#!/usr/bin/env python3
"""
Quality Metrics Dashboard - Superhuman Edition
==============================================
Collects and displays comprehensive quality metrics for the project.

Usage:
    python scripts/quality_metrics.py              # Show dashboard
    python scripts/quality_metrics.py --json       # Output JSON
    python scripts/quality_metrics.py --export     # Export to file
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


# Colors for terminal output
class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def run_command(cmd: str, capture_output: bool = True) -> tuple[int, str]:
    """Run shell command and return exit code and output.

    Note: shell=True is used here for convenience with pipe commands.
    All commands are hardcoded and controlled by this script (no user input),
    so there is no security risk.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,  # Safe: All commands are hardcoded, no user input
            capture_output=capture_output,
            text=True,
            timeout=120,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except Exception as e:
        return 1, str(e)


def get_code_metrics() -> dict[str, Any]:
    """Get code quality metrics."""
    metrics = {}

    # Count lines of code
    code, output = run_command(
        "find app/ -name '*.py' -not -path '*/migrations/*' -exec wc -l {} + | tail -1"
    )
    if code == 0:
        try:
            metrics["lines_of_code"] = int(output.split()[0])
        except:
            metrics["lines_of_code"] = 0

    # Count files
    code, output = run_command("find app/ -name '*.py' -not -path '*/migrations/*' | wc -l")
    if code == 0:
        try:
            metrics["python_files"] = int(output.strip())
        except:
            metrics["python_files"] = 0

    # Get Radon complexity
    code, output = run_command("radon cc app/ -a -s -j")
    if code == 0:
        try:
            complexity_data = json.loads(output)
            total_complexity = 0
            function_count = 0

            for file_data in complexity_data.values():
                for item in file_data:
                    if isinstance(item, dict) and "complexity" in item:
                        total_complexity += item["complexity"]
                        function_count += 1

            metrics["average_complexity"] = (
                round(total_complexity / function_count, 2) if function_count > 0 else 0
            )
            metrics["total_functions"] = function_count
        except:
            metrics["average_complexity"] = 0
            metrics["total_functions"] = 0

    # Get maintainability index
    code, output = run_command("radon mi app/ -s -j")
    if code == 0:
        try:
            mi_data = json.loads(output)
            mi_scores = []

            for file_data in mi_data.values():
                if isinstance(file_data, dict) and "mi" in file_data:
                    mi_scores.append(file_data["mi"])

            metrics["maintainability_index"] = (
                round(sum(mi_scores) / len(mi_scores), 2) if mi_scores else 0
            )
        except:
            metrics["maintainability_index"] = 0

    return metrics


def get_test_metrics() -> dict[str, Any]:
    """Get test coverage metrics."""
    metrics = {}

    # Run pytest with coverage
    code, output = run_command(
        "FLASK_ENV=testing TESTING=1 SECRET_KEY=test-key "
        "pytest --quiet --cov=app --cov-report=json --cov-report=term 2>&1"
    )

    # Parse coverage.json if it exists
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            metrics["coverage_percent"] = round(coverage_data["totals"]["percent_covered"], 2)
            metrics["lines_covered"] = coverage_data["totals"]["covered_lines"]
            metrics["lines_total"] = coverage_data["totals"]["num_statements"]
            metrics["branches_covered"] = coverage_data["totals"].get("covered_branches", 0)
            metrics["missing_lines"] = coverage_data["totals"]["missing_lines"]
        except Exception as e:
            print(f"Error parsing coverage: {e}")
            metrics["coverage_percent"] = 0
    else:
        metrics["coverage_percent"] = 0

    # Count test files and tests
    code, output = run_command("find tests/ -name 'test_*.py' | wc -l")
    if code == 0:
        try:
            metrics["test_files"] = int(output.strip())
        except:
            metrics["test_files"] = 0

    # Extract test count from pytest output
    if "passed" in output:
        try:
            # Look for pattern like "297 passed"
            import re

            match = re.search(r"(\d+)\s+passed", output)
            if match:
                metrics["total_tests"] = int(match.group(1))
            else:
                metrics["total_tests"] = 0
        except:
            metrics["total_tests"] = 0
    else:
        metrics["total_tests"] = 0

    return metrics


def get_security_metrics() -> dict[str, Any]:
    """Get security scan metrics."""
    metrics = {}

    # Run Bandit
    code, output = run_command("bandit -r app/ -c pyproject.toml -f json 2>&1")

    # Parse Bandit output
    try:
        # Extract severity counts
        import re

        high_match = re.search(r"High:\s+(\d+)", output)
        medium_match = re.search(r"Medium:\s+(\d+)", output)
        low_match = re.search(r"Low:\s+(\d+)", output)

        metrics["security_high"] = int(high_match.group(1)) if high_match else 0
        metrics["security_medium"] = int(medium_match.group(1)) if medium_match else 0
        metrics["security_low"] = int(low_match.group(1)) if low_match else 0
        metrics["security_total"] = (
            metrics["security_high"] + metrics["security_medium"] + metrics["security_low"]
        )
    except:
        metrics["security_high"] = 0
        metrics["security_medium"] = 0
        metrics["security_low"] = 0
        metrics["security_total"] = 0

    return metrics


def get_linting_metrics() -> dict[str, Any]:
    """Get linting metrics."""
    metrics = {}

    # Ruff
    code, output = run_command("ruff check app/ tests/ --output-format=json 2>&1")
    metrics["ruff_violations"] = 0 if code == 0 else output.count("\n")

    # Pylint
    code, output = run_command("pylint app/ --exit-zero --score=yes 2>&1")
    if code == 0:
        try:
            import re

            match = re.search(r"Your code has been rated at ([\d.]+)/10", output)
            if match:
                metrics["pylint_score"] = float(match.group(1))
            else:
                metrics["pylint_score"] = 0.0
        except:
            metrics["pylint_score"] = 0.0
    else:
        metrics["pylint_score"] = 0.0

    return metrics


def calculate_overall_score(metrics: dict[str, Any]) -> float:
    """Calculate overall quality score (0-100)."""
    scores = []

    # Coverage score (0-40 points)
    coverage = metrics.get("test", {}).get("coverage_percent", 0)
    coverage_score = min(40, (coverage / 80) * 40)  # 80% coverage = full points
    scores.append(coverage_score)

    # Pylint score (0-20 points)
    pylint = metrics.get("linting", {}).get("pylint_score", 0)
    pylint_score = (pylint / 10) * 20
    scores.append(pylint_score)

    # Security score (0-20 points)
    security_high = metrics.get("security", {}).get("security_high", 0)
    security_score = max(0, 20 - (security_high * 2))  # Each high issue = -2 points
    scores.append(security_score)

    # Complexity score (0-10 points)
    avg_complexity = metrics.get("code", {}).get("average_complexity", 0)
    complexity_score = max(0, 10 - (avg_complexity - 5))  # Ideal complexity ~5
    scores.append(complexity_score)

    # Maintainability score (0-10 points)
    maintainability = metrics.get("code", {}).get("maintainability_index", 0)
    maintainability_score = min(10, (maintainability / 100) * 10)
    scores.append(maintainability_score)

    return round(sum(scores), 2)


def display_dashboard(metrics: dict[str, Any]) -> None:
    """Display metrics dashboard."""
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.PURPLE}  🏆 SUPERHUMAN QUALITY METRICS DASHBOARD{Colors.NC}")
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print()

    # Overall Score
    overall_score = calculate_overall_score(metrics)
    score_color = (
        Colors.GREEN
        if overall_score >= 80
        else Colors.YELLOW
        if overall_score >= 60
        else Colors.RED
    )
    print(f"{Colors.CYAN}📊 Overall Quality Score: {score_color}{overall_score}/100{Colors.NC}")
    print()

    # Code Metrics
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}📝 Code Metrics{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    code = metrics.get("code", {})
    print(f"  Lines of Code:          {code.get('lines_of_code', 0):,}")
    print(f"  Python Files:           {code.get('python_files', 0)}")
    print(f"  Total Functions:        {code.get('total_functions', 0)}")
    print(f"  Average Complexity:     {code.get('average_complexity', 0)}")
    print(f"  Maintainability Index:  {code.get('maintainability_index', 0)}")
    print()

    # Test Metrics
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}🧪 Test Metrics{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    test = metrics.get("test", {})
    coverage = test.get("coverage_percent", 0)
    coverage_color = (
        Colors.GREEN if coverage >= 80 else Colors.YELLOW if coverage >= 30 else Colors.RED
    )
    print(f"  Test Files:             {test.get('test_files', 0)}")
    print(f"  Total Tests:            {test.get('total_tests', 0)}")
    print(f"  Coverage:               {coverage_color}{coverage}%{Colors.NC}")
    print(
        f"  Lines Covered:          {test.get('lines_covered', 0):,}/{test.get('lines_total', 0):,}"
    )
    print(f"  Missing Lines:          {test.get('missing_lines', 0):,}")
    print()

    # Security Metrics
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}🔒 Security Metrics{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    security = metrics.get("security", {})
    print(f"  {Colors.RED}High Severity:          {security.get('security_high', 0)}{Colors.NC}")
    print(
        f"  {Colors.YELLOW}Medium Severity:        {security.get('security_medium', 0)}{Colors.NC}"
    )
    print(f"  {Colors.GREEN}Low Severity:           {security.get('security_low', 0)}{Colors.NC}")
    print(f"  Total Issues:           {security.get('security_total', 0)}")
    print()

    # Linting Metrics
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}🔍 Linting Metrics{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 80}{Colors.NC}")
    linting = metrics.get("linting", {})
    pylint_score = linting.get("pylint_score", 0)
    pylint_color = (
        Colors.GREEN
        if pylint_score >= 8.0
        else Colors.YELLOW
        if pylint_score >= 6.0
        else Colors.RED
    )
    print(f"  Ruff Violations:        {linting.get('ruff_violations', 0)}")
    print(f"  Pylint Score:           {pylint_color}{pylint_score}/10.0{Colors.NC}")
    print()

    # Summary
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}📈 Quality Level: {score_color}", end="")
    if overall_score >= 80:
        print(f"SUPERHUMAN 🏆{Colors.NC}")
    elif overall_score >= 60:
        print(f"EXCELLENT ⭐{Colors.NC}")
    elif overall_score >= 40:
        print(f"GOOD ✅{Colors.NC}")
    else:
        print(f"NEEDS IMPROVEMENT ⚠️{Colors.NC}")
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Quality Metrics Dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--export", type=str, help="Export to file")
    args = parser.parse_args()

    print(f"{Colors.CYAN}Collecting quality metrics...{Colors.NC}")
    print()

    # Collect all metrics
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "code": get_code_metrics(),
        "test": get_test_metrics(),
        "security": get_security_metrics(),
        "linting": get_linting_metrics(),
    }

    # Add overall score
    metrics["overall_score"] = calculate_overall_score(metrics)

    # Output based on arguments
    if args.json:
        print(json.dumps(metrics, indent=2))
    elif args.export:
        with open(args.export, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"{Colors.GREEN}✅ Metrics exported to: {args.export}{Colors.NC}")
    else:
        display_dashboard(metrics)


if __name__ == "__main__":
    main()
