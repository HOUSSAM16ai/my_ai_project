# app/kernel.py
"""
The Reality Kernel for the CogniForge project.

This is the central point of the unified reality, where the application's
existence is defined. It bridges the old Flask world with the new FastAPI
world, ensuring a single, coherent application context.
"""

from fastapi import FastAPI

# ======================================================================================
# THE UNIFIED APPLICATION OBJECT
# ======================================================================================
# This is the single, unified application instance. All parts of the system,
# both new and legacy, will be rooted in this object.
app = FastAPI(
    title="CogniForge - Unified Reality Kernel",
    description="The single, coherent application instance for CogniForge.",
    version="1.0.0",
)

# ======================================================================================
# LEGACY BRIDGE
# ======================================================================================
# This section provides a compatibility layer for legacy components that
# still expect a Flask-like application context. It is a temporary measure
# until all components are migrated to the new reality.

# Further implementation will follow.
