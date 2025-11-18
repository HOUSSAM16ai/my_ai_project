# tests/test_cli_smoke.py
import os
import subprocess
import sys

import pytest
from click.testing import CliRunner

from app.cli import cli


@pytest.fixture
def test_db_path():
    """Provides a path to a temporary test database file and cleans it up."""
    db_path = os.path.abspath("test_cli_smoke.db")
    db_url = f"sqlite:///{db_path}"

    # Ensure the old DB file is gone before starting
    if os.path.exists(db_path):
        os.remove(db_path)

    yield db_url

    # Clean up the DB file after tests are done
    if os.path.exists(db_path):
        os.remove(db_path)


def setup_test_environment(db_url):
    """Sets up the environment variables for testing."""
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["ADMIN_EMAIL"] = "test@example.com"
    env["LOG_LEVEL"] = "INFO"
    env["SECRET_KEY"] = "test-secret-key"

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_root
    return env


def test_seed_dry_run_returns_zero_subprocess(test_db_path):
    """
    Tests the CLI seed command with --dry-run using a subprocess and a file DB.
    """
    env = setup_test_environment(test_db_path)

    # Create tables
    res_create = subprocess.run(
        [sys.executable, "-m", "app.cli", "db", "create-all"],
        env=env,
        capture_output=True,
        text=True,
    )
    print("STDOUT (create-all):", res_create.stdout)
    print("STDERR (create-all):", res_create.stderr)
    assert res_create.returncode == 0

    # Seed data
    res_seed = subprocess.run(
        [sys.executable, "-m", "app.cli", "db", "seed", "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
    )

    print("STDOUT (seed):", res_seed.stdout)
    print("STDERR (seed):", res_seed.stderr)

    assert res_seed.returncode == 0
    assert "dry-run: rolling back" in res_seed.stdout


def test_seed_dry_run_returns_zero_runner(test_db_path):
    """
    Tests the CLI seed command with --dry-run using CliRunner and a file DB.
    """
    runner = CliRunner()
    env = {
        "DATABASE_URL": test_db_path,
        "ADMIN_EMAIL": "test@example.com",
        "LOG_LEVEL": "INFO",
        "SECRET_KEY": "test-secret-key",
    }

    # Create tables
    result_create = runner.invoke(cli, ["db", "create-all"], env=env)
    assert result_create.exit_code == 0

    # Seed data
    result_seed = runner.invoke(cli, ["db", "seed", "--dry-run"], env=env)

    print("OUTPUT:", result_seed.output)

    assert result_seed.exit_code == 0
    assert "dry-run: rolling back" in result_seed.output
