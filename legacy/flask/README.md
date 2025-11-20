# Legacy Flask Artifacts

This directory contains code that was part of the legacy Flask architecture and has been removed from the active codebase.

## Removed Components

- `compat_collapse.py`: A compatibility layer that attempted to mimic Flask globals (`current_app`, `g`) in a FastAPI environment. This is no longer needed as the architecture is now pure FastAPI.
