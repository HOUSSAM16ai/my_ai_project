# app/overmind/planning/sandbox.py
# ======================================================================================
# PLANNER FACTORY SANDBOX - TRUE SUBPROCESS ISOLATION
# Version 5.0.0 - Secure Import Management
# ======================================================================================
"""
Secure sandbox for importing planner modules.
Uses subprocess isolation to prevent unsafe imports from blocking the main process.
"""

import importlib
import logging
import subprocess
import sys
from types import ModuleType
from typing import Optional

from .exceptions import SandboxImportError, SandboxTimeout

_logger = logging.getLogger("overmind.factory.sandbox")


def _validate_module_safety(module_name: str) -> bool:
    """
    Quick validation check for module name safety.
    Returns True if module appears safe to import.
    """
    # Reject obviously dangerous patterns
    dangerous_patterns = [
        "..",  # Path traversal
        "/",  # Absolute paths
        "\\",  # Windows paths
        ";",  # Command injection
        "&",  # Command chaining
        "|",  # Pipe injection
        "$",  # Variable expansion
        "`",  # Command substitution
    ]
    for pattern in dangerous_patterns:
        if pattern in module_name:
            return False
    return True


def import_in_sandbox(
    module_name: str, timeout_s: float = 2.0, use_subprocess: bool = True
) -> ModuleType:
    """
    Import a module with subprocess sandbox isolation.

    This function provides two modes:
    1. Subprocess mode (use_subprocess=True, default): Tests import in isolated subprocess
       before importing in main process. Prevents blocking imports.
    2. Direct mode (use_subprocess=False): Direct import with exception handling.

    Args:
        module_name: Fully qualified module name to import
        timeout_s: Maximum time to wait for subprocess import (default: 2.0s)
        use_subprocess: Whether to use subprocess validation (default: True)

    Returns:
        ModuleType: The imported module

    Raises:
        SandboxImportError: If import fails
        SandboxTimeout: If subprocess import times out

    Example:
        >>> mod = import_in_sandbox("app.overmind.planning.llm_planner", timeout_s=3.0)
    """
    # Validate module name for obvious security issues
    if not _validate_module_safety(module_name):
        raise SandboxImportError(
            module_name, "Module name contains potentially dangerous characters"
        )

    if not use_subprocess:
        # Direct import mode (backward compatibility)
        return _direct_import(module_name)

    # Subprocess validation mode (true sandbox)
    return _subprocess_validated_import(module_name, timeout_s)


def _direct_import(module_name: str) -> ModuleType:
    """
    Direct import without subprocess validation.
    Used for backward compatibility or when subprocess mode is disabled.
    """
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        _logger.error(f"Direct import failed for {module_name}: {exc}")
        raise SandboxImportError(module_name, str(exc))


def _subprocess_validated_import(module_name: str, timeout_s: float) -> ModuleType:
    """
    Import with subprocess validation (true sandbox).
    First validates import in subprocess, then imports in main process if safe.
    """
    # Step 1: Validate import in subprocess
    _validate_import_in_subprocess(module_name, timeout_s)

    # Step 2: If validation passed, import in main process
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        _logger.error(f"Main process import failed after subprocess validation: {exc}")
        raise SandboxImportError(module_name, str(exc))


def _validate_import_in_subprocess(module_name: str, timeout_s: float):
    """
    Validate that a module can be imported by testing in a subprocess.
    Raises exception if subprocess import fails or times out.
    """
    # Create Python code to test import
    test_code = f"import {module_name}; print('OK')"

    try:
        # Run in subprocess with timeout
        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            timeout=timeout_s,
            text=True,
        )

        # Check subprocess result
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            _logger.error(f"Subprocess import validation failed for {module_name}: {error_msg}")
            raise SandboxImportError(module_name, error_msg)

        # Subprocess succeeded
        _logger.debug(f"Subprocess validation passed for {module_name}")

    except subprocess.TimeoutExpired:
        _logger.error(f"Subprocess import validation timed out for {module_name}")
        raise SandboxTimeout(module_name, timeout_s)

    except Exception as exc:
        _logger.error(f"Subprocess validation error for {module_name}: {exc}")
        raise SandboxImportError(module_name, str(exc))


def safe_import(module_name: str, fallback: Optional[ModuleType] = None) -> Optional[ModuleType]:
    """
    Safe import wrapper that returns None (or fallback) on failure instead of raising.

    Args:
        module_name: Module to import
        fallback: Optional fallback value to return on failure

    Returns:
        Imported module or fallback value

    Example:
        >>> mod = safe_import("app.overmind.planning.llm_planner")
        >>> if mod is None:
        ...     print("Import failed")
    """
    try:
        return import_in_sandbox(module_name, timeout_s=2.0, use_subprocess=True)
    except (SandboxImportError, SandboxTimeout) as exc:
        _logger.warning(f"Safe import failed for {module_name}: {exc}")
        return fallback


__all__ = [
    "import_in_sandbox",
    "safe_import",
]
