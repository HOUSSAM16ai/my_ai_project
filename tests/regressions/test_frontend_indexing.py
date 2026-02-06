import pytest
from pathlib import Path
from app.services.overmind.planning.deep_indexer import build_index

def test_frontend_files_are_indexed():
    """
    Regression test for Admin File Counting Bug.
    Verifies that the build_index function includes the 'frontend' directory
    and successfully counts JS/TS files within it.
    """
    # 1. Ensure we are running from root or have correct path
    root_path = Path.cwd()
    frontend_path = root_path / "frontend"

    # Skip if frontend doesn't exist
    if not frontend_path.exists():
        pytest.skip("frontend directory not found")

    # 2. Build Index
    # Note: We run on current dir. This assumes the test runner is at repo root.
    analysis = build_index(".")

    # 3. Check for frontend files
    # The relative path in analysis is relative to the root passed to build_index
    frontend_files = [f for f in analysis.files if f.relative_path.startswith("frontend/")]

    # 4. Assertions
    # We expect at least some files from frontend.
    # We know 'frontend/next.config.js' exists and is a .js file.

    # Before the fix, this is 0.
    # After the fix, this should be > 0.

    assert len(frontend_files) > 0, (
        f"No frontend files found in analysis. Total files: {len(analysis.files)}. "
        f"Ensure 'frontend' is in target candidates."
    )

    # Specific check for next.config.js or similar
    next_config = next((f for f in frontend_files if "next.config.js" in f.relative_path), None)
    assert next_config is not None, "next.config.js not found in index"
