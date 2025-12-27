#!/usr/bin/env python3
"""
🏆 GitHub Actions Fix Validator
================================
Validates that all workflows have proper:
1. Self-monitoring prevention (if applicable)
2. Status verification in if: always() jobs
3. Explicit exit codes
4. Proper error handling

Built with ❤️ by Houssam Benmerah
"""

import sys
from pathlib import Path

import yaml


class Colors:
    """ANSI color codes"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class WorkflowValidator:
    """Validate GitHub Actions workflows"""

    def __init__(self):
        self.workflows_dir = Path(".github/workflows")
        self.issues = []
        self.warnings = []
        self.successes = []

    def print_header(self, text: str):
        """Print styled header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

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

    def check_self_monitoring(self, workflow_file: Path, workflow_data: dict) -> bool:
        """Check if monitor workflow prevents self-monitoring"""
        workflow_name = workflow_data.get("name", "")

        # Only check monitor workflows
        if "monitor" not in workflow_name.lower():
            return True

        print(f"\n🔍 Checking self-monitoring prevention in: {workflow_file.name}")

        # Check if it monitors workflow_run events
        on_config = workflow_data.get("on", {})
        if isinstance(on_config, dict):
            workflow_run = on_config.get("workflow_run", {})
            if workflow_run:
                # Should have a list of workflows to monitor
                workflows = workflow_run.get("workflows", [])
                if workflow_name in workflows:
                    self.print_error(
                        f"{workflow_file.name}: Monitors itself in workflow_run.workflows"
                    )
                    return False

        # Check for self-skip logic in jobs
        jobs = workflow_data.get("jobs", {})
        has_self_skip = False

        for _job_name, job_data in jobs.items():
            steps = job_data.get("steps", [])
            for step in steps:
                run_script = step.get("run", "")
                if (
                    isinstance(run_script, str)
                    and "WORKFLOW_NAME" in run_script
                    and workflow_name in run_script
                    and ("exit 0" in run_script or "Skipping self-monitoring" in run_script)
                ):
                    has_self_skip = True
                    break

        if has_self_skip:
            self.print_success(f"{workflow_file.name}: Has self-monitoring prevention")
            return True
        self.print_warning(
            f"{workflow_file.name}: No explicit self-monitoring prevention found"
        )
        return True  # Not critical for non-monitor workflows

    def check_status_verification(self, workflow_file: Path, workflow_data: dict) -> bool:
        """Check if jobs with if: always() verify dependent job status"""
        print(f"\n🔍 Checking status verification in: {workflow_file.name}")

        jobs = workflow_data.get("jobs", {})
        has_always_jobs = False
        all_verified = True

        for job_name, job_data in jobs.items():
            if_condition = job_data.get("if", "")

            # Check for jobs with if: always()
            if "always()" in str(if_condition):
                has_always_jobs = True
                needs = job_data.get("needs", [])

                if not needs:
                    continue  # No dependencies to verify

                # Check if job verifies status of dependencies
                steps = job_data.get("steps", [])
                has_verification = False

                for step in steps:
                    run_script = step.get("run", "")
                    if (
                        isinstance(run_script, str)
                        and "needs." in run_script
                        and ".result" in run_script
                        and ("failure" in run_script or "success" in run_script)
                    ):
                        has_verification = True
                        break

                if has_verification:
                    self.print_success(
                        f"{workflow_file.name} - Job '{job_name}': Has status verification"
                    )
                else:
                    self.print_warning(
                        f"{workflow_file.name} - Job '{job_name}': Missing status verification"
                    )
                    all_verified = False

        if not has_always_jobs:
            self.print_success(
                f"{workflow_file.name}: No if: always() jobs (verification not needed)"
            )

        return all_verified

    def check_explicit_exits(self, workflow_file: Path, workflow_data: dict) -> bool:
        """Check if critical steps have explicit exit codes"""
        print(f"\n🔍 Checking explicit exit codes in: {workflow_file.name}")

        jobs = workflow_data.get("jobs", {})
        critical_steps_checked = 0
        steps_with_exit = 0

        for _job_name, job_data in jobs.items():
            steps = job_data.get("steps", [])

            for step in steps:
                step_name = step.get("name", "")
                run_script = step.get("run", "")

                # Check critical steps (those that verify, test, or validate)
                is_critical = any(
                    keyword in step_name.lower()
                    for keyword in ["verify", "test", "validate", "check", "confirm", "success"]
                )

                if is_critical and isinstance(run_script, str):
                    critical_steps_checked += 1

                    # Check for explicit exit
                    if "exit 0" in run_script or "exit 1" in run_script:
                        steps_with_exit += 1

        if critical_steps_checked > 0:
            percentage = (steps_with_exit / critical_steps_checked) * 100
            if percentage >= 80:
                self.print_success(
                    f"{workflow_file.name}: {steps_with_exit}/{critical_steps_checked} critical steps have explicit exit codes ({percentage:.0f}%)"
                )
                return True
            self.print_warning(
                f"{workflow_file.name}: Only {steps_with_exit}/{critical_steps_checked} critical steps have explicit exit codes ({percentage:.0f}%)"
            )
            return False
        self.print_success(f"{workflow_file.name}: No critical steps requiring exit codes")
        return True

    def validate_workflow(self, workflow_file: Path) -> bool:
        """Validate a single workflow file"""
        try:
            with open(workflow_file) as f:
                workflow_data = yaml.safe_load(f)

            if not workflow_data:
                self.print_error(f"{workflow_file.name}: Empty workflow file")
                return False

            # Run all checks
            checks = [
                self.check_self_monitoring(workflow_file, workflow_data),
                self.check_status_verification(workflow_file, workflow_data),
                self.check_explicit_exits(workflow_file, workflow_data),
            ]

            return all(checks)

        except Exception as e:
            self.print_error(f"{workflow_file.name}: Validation error - {e}")
            return False

    def run_validation(self) -> int:
        """Run validation on all workflows"""
        self.print_header("🚀 GITHUB ACTIONS FIX VALIDATOR")
        print(f"{Colors.BOLD}Validating workflow fixes for 'Action Required' issues{Colors.ENDC}\n")

        if not self.workflows_dir.exists():
            self.print_error("Workflows directory not found!")
            return 1

        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml")
        )

        if not workflow_files:
            self.print_error("No workflow files found!")
            return 1

        print(f"Found {len(workflow_files)} workflow files\n")

        all_valid = True
        for workflow_file in sorted(workflow_files):
            if not self.validate_workflow(workflow_file):
                all_valid = False

        # Print summary
        self.print_header("📊 VALIDATION SUMMARY")

        print(f"{Colors.OKGREEN}✅ Successes: {len(self.successes)}{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  Warnings: {len(self.warnings)}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Errors: {len(self.issues)}{Colors.ENDC}\n")

        if self.issues:
            print(f"\n{Colors.FAIL}Critical Issues Found:{Colors.ENDC}")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings (Non-Critical):{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  • {warning}")

        print(f"\n{'=' * 70}\n")

        if all_valid and not self.issues:
            print(f"{Colors.OKGREEN}{Colors.BOLD}🏆 ALL VALIDATIONS PASSED!{Colors.ENDC}")
            print(
                f"{Colors.OKGREEN}Workflows are ready to eliminate 'Action Required' issues!{Colors.ENDC}\n"
            )
            return 0
        if self.warnings and not self.issues:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠️  VALIDATION PASSED WITH WARNINGS{Colors.ENDC}")
            print(
                f"{Colors.WARNING}Workflows should work, but improvements recommended{Colors.ENDC}\n"
            )
            return 0
        print(f"{Colors.FAIL}{Colors.BOLD}❌ VALIDATION FAILED{Colors.ENDC}")
        print(f"{Colors.FAIL}Please fix the critical issues above{Colors.ENDC}\n")
        return 1


def main():
    """Main entry point"""
    validator = WorkflowValidator()
    exit_code = validator.run_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
