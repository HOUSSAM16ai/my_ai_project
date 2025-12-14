import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Set

class GitAnalyzer:
    """Git History Analyzer"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def analyze_file_history(self, file_path: str) -> Dict[str, Any]:
        """Analyze file modification history"""
        try:
            # Total commits
            result = subprocess.run(
                ["git", "log", "--follow", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            total_commits = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Commits in last 6 months
            result_6m = subprocess.run(
                ["git", "log", "--follow", "--since=6 months ago", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commits_6m = len(result_6m.stdout.strip().split("\n")) if result_6m.stdout.strip() else 0

            # Commits in last 12 months
            result_12m = subprocess.run(
                ["git", "log", "--follow", "--since=12 months ago", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commits_12m = len(result_12m.stdout.strip().split("\n")) if result_12m.stdout.strip() else 0

            # Authors
            result_authors = subprocess.run(
                ["git", "log", "--follow", "--format=%an", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            authors = set(result_authors.stdout.strip().split("\n")) if result_authors.stdout.strip() else set()
            num_authors = len(authors)

            # Bugfix commits
            result_bugfix = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--oneline",
                    "--grep=fix",
                    "--grep=bug",
                    "--grep=hotfix",
                    "-i",
                    "--",
                    file_path,
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            bugfix_commits = len(result_bugfix.stdout.strip().split("\n")) if result_bugfix.stdout.strip() else 0

            # Branches (approximate - get unique branch names)
            result_branches = subprocess.run(
                ["git", "log", "--follow", "--all", "--format=%D", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            branches: Set[str] = set()
            if result_branches.stdout.strip():
                for line in result_branches.stdout.strip().split("\n"):
                    if line:
                        # Extract branch names from "HEAD -> main, origin/main" format
                        parts = [p.strip() for p in line.split(",")]
                        for part in parts:
                            if "origin/" in part or "->" in part:
                                continue
                            if part and not part.startswith("tag:"):
                                branches.add(part)

            return {
                "total_commits": total_commits,
                "commits_last_6months": commits_6m,
                "commits_last_12months": commits_12m,
                "num_authors": num_authors,
                "bugfix_commits": bugfix_commits,
                "branches_modified": len(branches),
            }

        except Exception as e:
            # Silence errors in non-git environments or timeouts
            # print(f"Warning: Git analysis failed for {file_path}: {e}", file=sys.stderr)
            return {
                "total_commits": 0,
                "commits_last_6months": 0,
                "commits_last_12months": 0,
                "num_authors": 0,
                "bugfix_commits": 0,
                "branches_modified": 0,
            }
