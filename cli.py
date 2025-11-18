# cli.py - The Unified Reality Command Line Interface
"""
This is the single entry point for all command-line operations in the
CogniForge project. It uses the Typer library for a clean, modern CLI
experience.

The application context required for database access and other services
is provided by the Reality Kernel and its engines, not by a legacy
Flask context.
"""

from app.cli.main import app as typer_app

# ======================================================================================
# UNIFIED CLI ENTRYPOINT
# ======================================================================================
# The main execution block is now clean and framework-agnostic. It directly
# invokes the Typer application. The necessary application context will be
# established by the engines when commands are executed.


@typer_app.callback()
def callback():
    """
    CogniForge Unified Reality CLI.
    """
    pass


if __name__ == "__main__":
    typer_app()
