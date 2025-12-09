#!/usr/bin/env python3
"""
Universal Repository Synchronization Protocol (URSP) v3.2 - "Mirror Gate"
High-performance synchronization engine for multi-provider repository mirroring.
Enforces "Exact Replica" consistency using strict Git mirroring protocols.

This script identifies the execution environment (GitHub Actions or GitLab CI)
to establish a Single Source of Truth (SSOT). It then forces the Target Repository
to match the SSOT exactly, including pruning deleted branches and tags.

Safety Mechanisms:
- Automatically unshallows repositories.
- Creates local tracking branches for all remote branches to prevent data loss.
- Validates sync via strict process exit codes.

Usage:
    python scripts/universal_repo_sync.py

Environment Variables:
    SYNC_GITHUB_TOKEN: GitHub Personal Access Token
    SYNC_GITHUB_ID: GitHub Repository ID
    SYNC_GITLAB_TOKEN: GitLab Personal Access Token
    SYNC_GITLAB_ID: GitLab Project ID

    # Automatically provided by CI environments:
    GITHUB_ACTIONS: "true" if running on GitHub
    GITLAB_CI: "true" if running on GitLab
"""

import contextlib
import logging
import os
import subprocess
import sys

import requests

# Configure High-Precision Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | URSP | %(levelname)s | %(message)s")
logger = logging.getLogger("URSP")


def get_env_var(name, default=None, required=True):
    val = os.environ.get(name, default)
    if not val and required:
        # For non-critical optional targets, we might want to just log warning
        pass
    return val


def run_command(command, cwd=None, sensitive_inputs=None, ignore_errors=False):
    """Executes a shell command with secure output handling."""
    cmd_str = " ".join(command)
    if sensitive_inputs:
        for sensitive in sensitive_inputs:
            if sensitive:
                cmd_str = cmd_str.replace(sensitive, "******")

    logger.info(f"Executing vector: {cmd_str}")

    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        logger.info("Vector execution successful.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            logger.warning(f"Vector execution failed (ignored): {e.stderr}")
            return None
        logger.error(f"Vector execution failed: {e.stderr}")
        raise


def resolve_github_url(token, repo_id):
    """Resolves GitHub repository URL using the Repository ID."""
    logger.info(f"Resolving GitHub target for ID: {repo_id}")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repositories/{repo_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        clone_url = data.get("clone_url")
        # Inject auth
        auth_url = clone_url.replace("https://", f"https://oauth2:{token}@")
        return auth_url
    except Exception as e:
        logger.error(f"Failed to resolve GitHub target: {e}")
        raise


def resolve_gitlab_url(token, project_id):
    """Resolves GitLab project URL using the Project ID."""
    logger.info(f"Resolving GitLab target for ID: {project_id}")
    headers = {"PRIVATE-TOKEN": token}
    url = f"https://gitlab.com/api/v4/projects/{project_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        http_url = data.get("http_url_to_repo")
        # Inject auth - GitLab supports oauth2 as user for tokens, or just the token as user
        # Format: https://oauth2:<token>@gitlab.com/...
        auth_url = http_url.replace("https://", f"https://oauth2:{token}@")
        return auth_url
    except Exception as e:
        logger.error(f"Failed to resolve GitLab target: {e}")
        raise


def ensure_complete_history():
    """
    Ensures the local repository has complete history and local branches for all remote branches.
    This is CRITICAL before running 'git push --prune', otherwise valid remote branches
    might be deleted because the local CI environment (detached HEAD) doesn't know about them.
    """
    logger.info("Validating repository history depth...")

    # 1. Unshallow if needed
    if os.path.exists(".git/shallow"):
        logger.warning("Repository is shallow. Initiating full history hydration...")
        with contextlib.suppress(Exception):
            run_command(["git", "fetch", "--unshallow"], ignore_errors=True)

    # 2. Fetch all remotes
    logger.info("Fetching all remotes to ensure consistency...")
    run_command(["git", "fetch", "--all"], ignore_errors=True)

    # 3. Create local tracking branches for all remote branches
    # This prevents 'git push --prune +refs/heads/*:refs/heads/*' from deleting branches
    # that exist on origin but are not currently checked out locally.
    logger.info("Hydrating local tracking branches for all remote refs...")
    try:
        # Get all remote branches (excluding HEAD)
        output = run_command(["git", "branch", "-r"], ignore_errors=True)
        if output:
            for line in output.splitlines():
                branch = line.strip()
                if "->" in branch or "origin/HEAD" in branch:
                    continue

                # branch is like 'origin/feature/abc'
                # Use split to avoid replacing 'origin/' inside the branch name
                parts = branch.split("/", 1)
                if len(parts) == 2 and parts[0] == "origin":
                    local_branch_name = parts[1]
                else:
                    # Fallback or weird naming, skip to be safe
                    logger.warning(f"Skipping malformed branch ref: {branch}")
                    continue

                # Create local branch if it doesn't exist
                # git branch --track <local> <remote>
                # We use --force to update it if it exists but is stale
                logger.info(f"Tracking branch: {local_branch_name} -> {branch}")
                run_command(["git", "branch", "--track", "-f", local_branch_name, branch], ignore_errors=True)

    except Exception as e:
        logger.warning(f"Failed to hydrate some branches: {e}")


def sync_remotes():
    # 0. Safety Pre-flight
    ensure_complete_history()

    # 1. Identify Environment & Source of Truth
    is_github = os.environ.get("GITHUB_ACTIONS") == "true"
    is_gitlab = os.environ.get("GITLAB_CI") == "true"

    if is_github:
        logger.info("Detected Environment: GitHub Actions. Source of Truth: GitHub.")
        target_platform = "GitLab"
    elif is_gitlab:
        logger.info("Detected Environment: GitLab CI. Source of Truth: GitLab.")
        target_platform = "GitHub"
    else:
        logger.warning("Unknown environment. Defaulting to multi-target push mode.")
        target_platform = "All"

    # 2. Load Credentials
    github_token = os.environ.get("SYNC_GITHUB_TOKEN")
    github_id = os.environ.get("SYNC_GITHUB_ID")
    gitlab_token = os.environ.get("SYNC_GITLAB_TOKEN")
    gitlab_id = os.environ.get("SYNC_GITLAB_ID")

    # 3. Execute Synchronization based on Direction

    # CASE A: GitHub -> GitLab
    if (target_platform == "GitLab" or target_platform == "All") and gitlab_token and gitlab_id:
        try:
            target_url = resolve_gitlab_url(gitlab_token, gitlab_id)
            logger.info("Initiating Mirror Push to GitLab...")

            # Use --prune --force --all to ensure exact replica (deletes removed branches)
            # and --tags to sync tags.
            # Now that we have hydrated local branches, this is safe.
            run_command(
                ["git", "push", "--prune", "--force", target_url, "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*"],
                sensitive_inputs=[gitlab_token]
            )
            logger.info("✅ Sync to GitLab Successful (Exit Code 0).")

        except Exception as e:
            logger.error(f"Sync to GitLab failed: {e}")
            if target_platform == "GitLab":
                sys.exit(1)

    # CASE B: GitLab -> GitHub
    if (target_platform == "GitHub" or target_platform == "All") and github_token and github_id:
        try:
            target_url = resolve_github_url(github_token, github_id)
            logger.info("Initiating Mirror Push to GitHub...")

            run_command(
                ["git", "push", "--prune", "--force", target_url, "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*"],
                sensitive_inputs=[github_token]
            )
            logger.info("✅ Sync to GitHub Successful (Exit Code 0).")

        except Exception as e:
            logger.error(f"Sync to GitHub failed: {e}")
            if target_platform == "GitHub":
                sys.exit(1)

    logger.info("Universal synchronization protocol completed.")


if __name__ == "__main__":
    sync_remotes()
