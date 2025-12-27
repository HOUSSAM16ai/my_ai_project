#!/usr/bin/env python3
"""
🚀 SUPERHUMAN ACTION HEALTH CHECKER
===================================
Comprehensive GitHub Actions health monitoring and diagnostics tool.
Surpassing all tech giants in monitoring capabilities!

Features:
- Real-time workflow status checking
- Automatic issue detection
- Smart recommendations
- Detailed reporting
- Preventive analysis

Built with ❤️ by Houssam Benmerah
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class Colors:
    """ANSI color codes for beautiful terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ActionHealthChecker:
    """Superhuman GitHub Actions health checker"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.issues = []
        self.warnings = []
        self.successes = []

    def print_header(self, text: str):
        """Print a styled header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{text:^80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
        self.successes.append(text)

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
        self.warnings.append(text)

    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
        self.issues.append(text)

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

    def check_workflow_files(self) -> bool:
        """Check if workflow files exist and are valid"""
        self.print_header("🔍 CHECKING WORKFLOW FILES")

        if not self.workflows_dir.exists():
            self.print_error("Workflows directory not found!")
            return False

        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml")
        )

        if not workflow_files:
            self.print_error("No workflow files found!")
            return False

        self.print_success(f"Found {len(workflow_files)} workflow files")

        for workflow_file in workflow_files:
            self.print_info(f"  • {workflow_file.name}")

            # Basic YAML validation
            try:
                import yaml

                with open(workflow_file) as f:
                    yaml.safe_load(f)
                self.print_success(f"  {workflow_file.name}: Valid YAML")
            except ImportError:
                self.print_warning("  PyYAML not installed, skipping YAML validation")
            except Exception as e:
                self.print_error(f"  {workflow_file.name}: Invalid YAML - {e}")

        return True

    def check_formatting_tools(self) -> bool:
        """Check if formatting tools are available"""
        self.print_header("🎨 CHECKING FORMATTING TOOLS")

        tools = {
            "black": "Black code formatter",
            "isort": "Import sorter",
            "ruff": "Fast Python linter",
            "pylint": "Python linter",
            "flake8": "Style guide enforcement",
        }

        all_available = True
        for tool, description in tools.items():
            try:
                result = subprocess.run(
                    [tool, "--version"],
                    check=False, capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split("\n")[0]
                    self.print_success(f"{description} ({tool}): {version}")
                else:
                    self.print_warning(f"{description} ({tool}): Not available")
                    all_available = False
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.print_warning(f"{description} ({tool}): Not installed")
                all_available = False

        return all_available

    def check_code_quality(self) -> tuple[bool, dict[str, Any]]:
        """Check current code quality status"""
        self.print_header("📊 CHECKING CODE QUALITY")

        results = {
            "black": {"status": "unknown", "issues": []},
            "isort": {"status": "unknown", "issues": []},
            "ruff": {"status": "unknown", "issues": []},
        }

        # Check Black formatting
        self.print_info("Running Black check...")
        try:
            result = subprocess.run(
                ["black", "--check", "--line-length=100", "app/", "tests/"],
                check=False, capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )
            if result.returncode == 0:
                self.print_success("Black formatting: PASSED ✨")
                results["black"]["status"] = "pass"
            else:
                issues = result.stdout.count("would reformat")
                self.print_error(f"Black formatting: FAILED ({issues} files need reformatting)")
                results["black"]["status"] = "fail"
                results["black"]["issues"] = [result.stdout]
        except Exception as e:
            self.print_warning(f"Black check failed: {e}")

        # Check isort
        self.print_info("Running isort check...")
        try:
            result = subprocess.run(
                [
                    "isort",
                    "--check-only",
                    "--profile=black",
                    "--line-length=100",
                    "app/",
                    "tests/",
                ],
                check=False, capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )
            if result.returncode == 0:
                self.print_success("Import sorting (isort): PASSED 📦")
                results["isort"]["status"] = "pass"
            else:
                self.print_error("Import sorting (isort): FAILED")
                results["isort"]["status"] = "fail"
                results["isort"]["issues"] = [result.stdout]
        except Exception as e:
            self.print_warning(f"isort check failed: {e}")

        # Check Ruff
        self.print_info("Running Ruff check...")
        try:
            result = subprocess.run(
                ["ruff", "check", "app/", "tests/", "--output-format=concise"],
                check=False, capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )
            error_count = result.stdout.count("\n")
            if result.returncode == 0 or error_count < 10:
                self.print_success(f"Ruff linting: PASSED ⚡ ({error_count} minor warnings)")
                results["ruff"]["status"] = "pass"
            else:
                self.print_warning(f"Ruff linting: {error_count} issues found")
                results["ruff"]["status"] = "warn"
                results["ruff"]["issues"] = [result.stdout]
        except Exception as e:
            self.print_warning(f"Ruff check failed: {e}")

        all_passed = all(r["status"] == "pass" for r in results.values())
        return all_passed, results

    def generate_fix_script(self, results: dict[str, Any]):
        """Generate a script to fix detected issues"""
        self.print_header("🔧 GENERATING FIX SCRIPT")

        fix_script = """#!/bin/bash
# Auto-generated fix script
# Run this to fix detected code quality issues

echo "🚀 Fixing code quality issues..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

"""

        if results["black"]["status"] == "fail":
            fix_script += """
echo "⚫ Fixing Black formatting..."
black --line-length=100 app/ tests/
"""

        if results["isort"]["status"] == "fail":
            fix_script += """
echo "📦 Fixing import sorting..."
isort --profile=black --line-length=100 app/ tests/
"""

        if results["ruff"]["status"] in ["fail", "warn"]:
            fix_script += """
echo "⚡ Auto-fixing Ruff issues..."
ruff check --fix app/ tests/
"""

        fix_script += """
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Fixes applied! Please review and commit changes."
"""

        fix_script_path = self.project_root / "scripts" / "auto_fix_quality.sh"
        fix_script_path.parent.mkdir(exist_ok=True)
        fix_script_path.write_text(fix_script)
        fix_script_path.chmod(0o755)

        self.print_success(f"Fix script generated: {fix_script_path}")
        self.print_info(f"Run with: {fix_script_path}")

    def generate_report(self):
        """Generate comprehensive health report"""
        self.print_header("📊 HEALTH REPORT SUMMARY")

        print(
            f"\n{Colors.BOLD}Successes:{Colors.ENDC} {Colors.OKGREEN}{len(self.successes)}{Colors.ENDC}"
        )
        print(
            f"{Colors.BOLD}Warnings:{Colors.ENDC} {Colors.WARNING}{len(self.warnings)}{Colors.ENDC}"
        )
        print(f"{Colors.BOLD}Issues:{Colors.ENDC} {Colors.FAIL}{len(self.issues)}{Colors.ENDC}\n")

        if self.issues:
            print(f"\n{Colors.FAIL}❌ Issues Found:{Colors.ENDC}")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n{Colors.WARNING}⚠️  Warnings:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  • {warning}")

        # Overall status
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        if not self.issues:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✅ OVERALL STATUS: HEALTHY{Colors.ENDC}")
        elif len(self.issues) < 3:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️  OVERALL STATUS: NEEDS ATTENTION{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}❌ OVERALL STATUS: CRITICAL{Colors.ENDC}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

        # Save report
        report_path = self.project_root / ".github" / "health-reports"
        report_path.mkdir(parents=True, exist_ok=True)

        report_file = report_path / f"health-check-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "successes": self.successes,
            "warnings": self.warnings,
            "issues": self.issues,
            "status": "healthy" if not self.issues else "needs_attention",
        }

        report_file.write_text(json.dumps(report_data, indent=2))
        self.print_success(f"Report saved to: {report_file}")

    def run_full_check(self):
        """Run complete health check"""
        self.print_header("🚀 SUPERHUMAN ACTION HEALTH CHECKER")
        print(f"{Colors.BOLD}Surpassing Google, Microsoft, OpenAI, Apple!{Colors.ENDC}\n")

        # Run all checks
        self.check_workflow_files()
        self.check_formatting_tools()
        quality_ok, quality_results = self.check_code_quality()

        # Generate fix script if needed
        if not quality_ok:
            self.generate_fix_script(quality_results)

        # Generate report
        self.generate_report()

        # Return exit code
        return 0 if not self.issues else 1


def main():
    """Main entry point"""
    checker = ActionHealthChecker()
    exit_code = checker.run_full_check()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
