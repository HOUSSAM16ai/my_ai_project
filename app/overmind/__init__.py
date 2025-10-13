# app/overmind/__init__.py
# ======================================================================================
# ==                             THE OVERMIND SYSTEM CORE                             ==
# ======================================================================================
#
# ⚔ PURPOSE (القصد):
#   This file establishes the `overmind` package and serves as its primary public
#   interface. It exposes the key components and services from the sub-packages,
#   providing a clean, unified entry point for the rest of the application.
#
#   By importing from here (e.g., `from app.overmind import orchestrator`), other parts
#   of the system do not need to know the internal structure of the Overmind package,
#   making our architecture more modular and easier to refactor in the future.
#
# 🧬 EXPORTS (الصادرات):
#   - orchestrator: The main service for running missions.
#   - planning: Access to the planning sub-system (e.g., for getting planners).
#   - schemas: Core Pydantic schemas for tasks and plans.
#
# ===============================================================================

# --- [FUTURE] Import and expose the main orchestrator service ---
# When you create `orchestrator.py`, you will uncomment this line.
# from . import orchestrator

# --- Import and expose the entire planning sub-package ---
from . import planning

# --- Import and expose the core schemas for easy access ---
from .planning import schemas

# --- Define what is publicly available when someone does `from app.overmind import *` ---
__all__ = [
    # "orchestrator", # Uncomment when ready
    "planning",
    "schemas",
]
