import subprocess


def test_integration_flag_registered():
    """
    Verifies that the --run-integration flag is correctly registered in pytest
    and prevents the ValueError crash in test_ai_gateway_smoke.py.
    """

    # Run pytest on the specific file that was crashing
    # We expect it to run (and potentially fail or skip) but NOT crash with an internal error (exit code 2/3/4/5 depending on pytest version for collected errors)
    # If it skips, exit code is 0 (if no other tests fail)
    # If it fails assertions, exit code is 1.
    # If it errors during collection (like ValueError), exit code is usually non-zero/non-one (often 2, 3, 4).

    # We run with -v to see output
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/gateways/test_ai_gateway_smoke.py::test_ai_gateway_integration", "-vv"],
        capture_output=True,
        text=True
    )

    # Check that we didn't get the ValueError
    assert "ValueError: no option named '--run-integration'" not in result.stderr
    assert "ValueError: no option named '--run-integration'" not in result.stdout

    # The test should be skipped by default
    assert "SKIPPED" in result.stdout or "SKIPPED" in result.stderr

    # Now run with the flag
    result_with_flag = subprocess.run(
        ["python", "-m", "pytest", "tests/gateways/test_ai_gateway_smoke.py::test_ai_gateway_integration", "--run-integration", "-vv"],
        capture_output=True,
        text=True
    )

    # Should not have ValueError
    assert "ValueError: no option named '--run-integration'" not in result_with_flag.stderr

    # It might fail the actual test logic because of missing dependencies, but that means the flag worked!
    # We look for "FAILED" (assertion error) not "ERROR" (collection/setup error)
    # Note: pytest treats setup errors as ERROR. The ValueError happened at setup/collection.
    # If the test fails because "Exception" was not raised, that's a failure, not an error.

    if result_with_flag.returncode != 0:
         # Ensure it wasn't a collection error
         assert "ValueError" not in result_with_flag.stderr
