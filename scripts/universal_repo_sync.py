#!/usr/bin/env python3
"""
Universal Repository Synchronization Protocol (URSP)
High-performance synchronization engine for multi-provider repository mirroring.

This script uses provided authentication tokens and repository IDs to resolve
target repository URLs via their respective APIs and performs a force-push
synchronization to ensure state consistency across the intelligence network.

It automatically handles the detached HEAD state common in CI/CD environments
by identifying the triggering reference (branch or tag) and pushing explicitly.
It supports both GitHub Actions and GitLab CI environments.

Usage:
    python scripts/universal_repo_sync.py

Environment Variables:
    SYNC_GITHUB_TOKEN: GitHub Personal Access Token
    SYNC_GITHUB_ID: GitHub Repository ID
    SYNC_GITLAB_TOKEN: GitLab Personal Access Token
    SYNC_GITLAB_ID: GitLab Project ID

    # Automatically provided by CI environments:
    GITHUB_REF: (GitHub Actions) The full ref that triggered the workflow (e.g., refs/heads/main)
    CI_COMMIT_REF_NAME: (GitLab CI) The branch or tag name (e.g., main)
    CI_COMMIT_SHA: (GitLab CI) The commit revision
"""

import logging
import os
import subprocess
import sys

import requests

# Configure High-Precision Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | URSP | %(levelname)s | %(message)s")
logger = logging.getLogger("URSP")


def get_env_var(name, default=None):
    val = os.environ.get(name, default)
    if not val and default is None:
        logger.error(f"Critical protocol failure: Missing environment variable {name}")
        sys.exit(1)
    return val


def run_command(command, cwd=None, sensitive_inputs=None):
    """Executes a shell command with secure output handling."""
    cmd_str = " ".join(command)
    if sensitive_inputs:
        for sensitive in sensitive_inputs:
            cmd_str = cmd_str.replace(sensitive, "******")

    logger.info(f"Executing vector: {cmd_str}")

    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        logger.info("Vector execution successful.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Vector execution failed: {e.stderr}")
        raise


def resolve_github_target(token, repo_id):
    """Resolves GitHub repository URL using the Repository ID via GitHub API."""
    logger.info(f"Resolving GitHub target for ID: {repo_id}")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repositories/{repo_id}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        clone_url = data.get("clone_url")
        full_name = data.get("full_name")
        logger.info(f"Target resolved: {full_name}")

        # Inject auth into URL
        auth_url = clone_url.replace("https://", f"https://oauth2:{token}@")
        return auth_url
    except Exception as e:
        logger.error(f"Failed to resolve GitHub target: {e}")
        raise


def resolve_gitlab_target(token, project_id):
    """Resolves GitLab project URL using the Project ID via GitLab API."""
    logger.info(f"Resolving GitLab target for ID: {project_id}")
    headers = {"PRIVATE-TOKEN": token}
    url = f"https://gitlab.com/api/v4/projects/{project_id}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        http_url = data.get("http_url_to_repo")
        name = data.get("path_with_namespace")
        logger.info(f"Target resolved: {name}")

        # Inject auth into URL
        # For GitLab token auth, use oauth2:token or just user:token.
        # Using 'oauth2' as username is standard for Bearer tokens in some contexts,
        # but for private tokens, usually just the string is enough as password.
        # We will use the format https://oauth2:<token>@gitlab.com/...
        auth_url = http_url.replace("https://", f"https://oauth2:{token}@")
        return auth_url
    except Exception as e:
        logger.error(f"Failed to resolve GitLab target: {e}")
        raise


def determine_push_spec():
    """
    Determines the git push specification based on the current CI environment.
    Returns a string like 'HEAD:refs/heads/main' or '--all'.
    """
    # 1. GitHub Actions
    github_ref = os.environ.get("GITHUB_REF")
    if github_ref:
        logger.info(f"Detected GitHub Actions environment. Ref: {github_ref}")
        return f"HEAD:{github_ref}"

    # 2. GitLab CI
    gitlab_ref_name = os.environ.get("CI_COMMIT_REF_NAME")
    if gitlab_ref_name:
        logger.info(f"Detected GitLab CI environment. Branch/Tag: {gitlab_ref_name}")
        # GitLab CI usually checks out the specific commit in detached HEAD.
        # We need to construct the full ref.
        # We can try to guess if it's a tag or branch, but usually pushing to refs/heads/NAME is safe for branches.
        # However, CI_COMMIT_TAG exists if it is a tag.
        gitlab_tag = os.environ.get("CI_COMMIT_TAG")
        if gitlab_tag:
            return f"HEAD:refs/tags/{gitlab_tag}"
        else:
            return f"HEAD:refs/heads/{gitlab_ref_name}"

    logger.warning(
        "No standard CI environment detected. Defaulting to mirroring all local branches."
    )
    return "--all"


def sync_remotes():
    github_token = get_env_var("SYNC_GITHUB_TOKEN")
    github_id = get_env_var("SYNC_GITHUB_ID")
    gitlab_token = get_env_var("SYNC_GITLAB_TOKEN")
    gitlab_id = get_env_var("SYNC_GITLAB_ID")

    push_spec = determine_push_spec()

    # 1. Resolve Targets
    try:
        github_url = resolve_github_target(github_token, github_id)
        gitlab_url = resolve_gitlab_target(gitlab_token, gitlab_id)
    except Exception:
        # Fixed: Removed unused variable 'e'
        logger.error("Target resolution aborted.")
        sys.exit(1)

    # 2. Push to GitHub
    logger.info("Initiating GitHub synchronization sequence...")
    try:
        run_command(
            ["git", "push", "--force", github_url, push_spec], sensitive_inputs=[github_token]
        )
        if push_spec == "--all":
            run_command(
                ["git", "push", "--force", github_url, "--tags"], sensitive_inputs=[github_token]
            )
    except Exception:
        logger.error("GitHub sync failed.")

    # 3. Push to GitLab
    logger.info("Initiating GitLab synchronization sequence...")
    try:
        run_command(
            ["git", "push", "--force", gitlab_url, push_spec], sensitive_inputs=[gitlab_token]
        )
        if push_spec == "--all":
            run_command(
                ["git", "push", "--force", gitlab_url, "--tags"], sensitive_inputs=[gitlab_token]
            )
    except Exception:
        logger.error("GitLab sync failed.")

    logger.info("Universal synchronization protocol completed.")


if __name__ == "__main__":
    sync_remotes()
