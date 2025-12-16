import os
import stat
from pathlib import Path

def test_setup_dev_script_integrity():
    """
    Regression Test: Verify that scripts/setup_dev.sh exists and contains
    critical logic for the 'Superhuman' development environment.

    This ensures that:
    1. The script handles port visibility (critical for Codespaces).
    2. The script implements an auto-restart loop.
    3. The script handles secret/env generation.
    """
    script_path = Path("scripts/setup_dev.sh")

    # 1. Existence Check
    assert script_path.exists(), "scripts/setup_dev.sh must exist"

    # 2. Permission Check
    st = os.stat(script_path)
    assert bool(st.st_mode & stat.S_IXUSR), "scripts/setup_dev.sh must be executable"

    content = script_path.read_text(encoding="utf-8")

    # 3. Critical Logic Checks

    # Visibility: The core fix for "environment stops / no notification"
    assert "gh codespace ports visibility 8000:public" in content, \
        "Script must enforce public port visibility for Codespaces automation"

    # Robustness: Must kill stale processes
    assert "kill -9 $PID" in content, "Script must clean up stale processes on port 8000"

    # Resilience: Must use a loop
    assert "while true; do" in content, "Script must run in an infinite loop"

    # Safety: Must handle crashes in the loop
    assert "|| true" in content, "Script must use '|| true' to prevent exit on crash in set -e mode"

    # Config: Must handle .env generation
    assert "DATABASE_URL=sqlite+aiosqlite:///./dev.db" in content, "Script must provide default .env configuration"

    # Dependencies: Must check requirements
    assert "pip install -r requirements.txt" in content, "Script must verify dependencies"
