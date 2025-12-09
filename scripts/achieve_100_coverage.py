#!/usr/bin/env python3
"""
Script to Achieve 100% Test Coverage
=====================================

This script analyzes the current coverage and generates test files
for all uncovered modules to achieve 100% coverage.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_coverage_analysis() -> dict:
    """Run pytest with coverage and return results"""
    print("🔍 Running coverage analysis...")

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=json:coverage_analysis.json",
        "--cov-report=term-missing",
        "-q",
        "--tb=no",
    ]

    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("⚠️  Coverage analysis timed out")

    # Read coverage data
    coverage_file = Path("coverage_analysis.json")
    if coverage_file.exists():
        with open(coverage_file) as f:
            return json.load(f)
    return {}


def analyze_coverage(coverage_data: dict) -> tuple[list[str], list[tuple[str, float]]]:
    """Analyze coverage data and return uncovered and low-coverage files"""
    if not coverage_data or "files" not in coverage_data:
        return [], []

    files = coverage_data["files"]

    zero_coverage = []
    low_coverage = []

    for filepath, metrics in files.items():
        if not filepath.startswith("app/"):
            continue

        # Skip certain files
        if any(
            skip in filepath for skip in ["__pycache__", "migrations/", "__init__.py", "main.py"]
        ):
            continue

        coverage_pct = metrics["summary"]["percent_covered"]

        if coverage_pct == 0:
            zero_coverage.append(filepath)
        elif coverage_pct < 100:
            low_coverage.append((filepath, coverage_pct))

    return zero_coverage, low_coverage


def generate_test_template(module_path: str) -> str:
    """Generate a test file template for a module"""
    module_name = Path(module_path).stem

    template = f'''"""
Comprehensive Tests for {module_name}
{"=" * (25 + len(module_name))}

Auto-generated test template.
Target: 100% coverage

TODO:
- Analyze module functions and classes
- Add unit tests for all functions
- Add edge case tests
- Add property-based tests if applicable
- Add integration tests if needed
"""

import pytest

# Import the module to test
# from app.{module_path.replace("app/", "").replace(".py", "").replace("/", ".")} import *


class Test{module_name.title().replace("_", "")}:
    """Test class for {module_name}"""

    def test_placeholder(self):
        """Placeholder test - replace with actual tests"""
        # TODO: Implement actual tests
        assert True


# Add more test classes as needed
'''

    return template


def create_test_files(zero_coverage: list[str], low_coverage: list[tuple[str, float]]):
    """Create test file templates for uncovered modules"""
    print("\n📝 Creating test file templates...")

    created = 0

    for module_path in zero_coverage[:10]:  # Limit to first 10
        # Convert app/module/file.py to tests/module/test_file_comprehensive.py
        parts = Path(module_path).parts[1:]  # Remove 'app'
        test_dir = Path("tests") / Path(*parts[:-1])
        test_file = test_dir / f"test_{parts[-1].replace('.py', '')}_comprehensive.py"

        # Create directory if needed
        test_dir.mkdir(parents=True, exist_ok=True)

        # Create test file if it doesn't exist
        if not test_file.exists():
            template = generate_test_template(module_path)
            test_file.write_text(template)
            print(f"  ✅ Created: {test_file}")
            created += 1
        else:
            print(f"  ⏭️  Exists: {test_file}")

    print(f"\n📊 Created {created} new test file templates")


def print_coverage_report(
    coverage_data: dict, zero_coverage: list[str], low_coverage: list[tuple[str, float]]
):
    """Print a detailed coverage report"""
    print("\n" + "=" * 70)
    print("📊 COVERAGE ANALYSIS REPORT")
    print("=" * 70)

    if "totals" in coverage_data:
        totals = coverage_data["totals"]
        total_coverage = totals["percent_covered"]
        covered_lines = totals["covered_lines"]
        total_lines = totals["num_statements"]

        print("\n📈 Overall Coverage:")
        print(f"  Total Lines: {total_lines}")
        print(f"  Covered Lines: {covered_lines}")
        print(f"  Coverage: {total_coverage:.2f}%")

        if total_coverage >= 100:
            print("  🎉 100% COVERAGE ACHIEVED!")
        elif total_coverage >= 90:
            print(f"  🟡 {100 - total_coverage:.2f}% away from 100%")
        else:
            print(f"  🔴 {100 - total_coverage:.2f}% away from 100%")

    print(f"\n📁 Files with 0% Coverage: {len(zero_coverage)}")
    if zero_coverage:
        print("  Top 10:")
        for filepath in zero_coverage[:10]:
            print(f"    - {filepath}")

    print(f"\n📁 Files with <100% Coverage: {len(low_coverage)}")
    if low_coverage:
        print("  Top 10:")
        for filepath, coverage in sorted(low_coverage, key=lambda x: x[1])[:10]:
            print(f"    - {filepath}: {coverage:.1f}%")

    print("\n" + "=" * 70)


def generate_action_plan(zero_coverage: list[str], low_coverage: list[tuple[str, float]]):
    """Generate an action plan to achieve 100% coverage"""
    print("\n📋 ACTION PLAN TO ACHIEVE 100% COVERAGE")
    print("=" * 70)

    total_files = len(zero_coverage) + len(low_coverage)
    print(f"\n🎯 Total files needing work: {total_files}")

    print("\n🔴 Priority 1: Files with 0% coverage")
    print(f"   Count: {len(zero_coverage)}")
    print("   Action: Create comprehensive test files")

    print("\n🟡 Priority 2: Files with <100% coverage")
    print(f"   Count: {len(low_coverage)}")
    print("   Action: Add tests for uncovered lines")

    print("\n📝 Recommended Steps:")
    print("   1. Run: ./scripts/achieve_100_coverage.py")
    print("   2. Fill in generated test templates")
    print("   3. Run: pytest --cov=app --cov-report=term-missing")
    print("   4. Identify uncovered lines and add tests")
    print("   5. Run mutation testing: mutmut run")
    print("   6. Repeat until 100% coverage + 100% mutation score")

    print("\n" + "=" * 70)


def main():
    """Main execution"""
    print("🚀 Starting 100% Coverage Achievement Script")
    print("=" * 70)

    # Step 1: Run coverage analysis
    coverage_data = run_coverage_analysis()

    if not coverage_data:
        print("❌ Failed to generate coverage data")
        sys.exit(1)

    # Step 2: Analyze coverage
    zero_coverage, low_coverage = analyze_coverage(coverage_data)

    # Step 3: Print report
    print_coverage_report(coverage_data, zero_coverage, low_coverage)

    # Step 4: Generate action plan
    generate_action_plan(zero_coverage, low_coverage)

    # Step 5: Create test templates
    if zero_coverage:
        response = input("\n❓ Create test file templates? (y/n): ")
        if response.lower() == "y":
            create_test_files(zero_coverage, low_coverage)

    print("\n✅ Analysis complete!")
    print("📁 Next: Fill in test templates and run tests")


if __name__ == "__main__":
    main()
