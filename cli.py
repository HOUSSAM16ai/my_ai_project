# cli.py - The World-Awakening Entrypoint (v2.0)

import os

from app import create_app
from app.cli.main import app as typer_app

# --- [THE WORLD-AWAKENING PROTOCOL] ---
# STEP 1: We forge a minimal instance of our Flask application.
# This is necessary to create an "application context," which makes core
# components like the database (db) and configuration (current_app.config)
# available to our CLI commands and the services they call.
# We default to the 'development' configuration for CLI operations.
flask_app = create_app(os.getenv("FLASK_ENV", "development"))


# STEP 2: We define a master callback for our Typer application.
# This function's docstring will appear as the main help text for the CLI.
@typer_app.callback()
def callback():
    """
    CogniForge Supercharged CLI - Your repo-native architect.
    A toolkit for indexing, searching, and reasoning about the codebase.
    """
    pass


# STEP 3: We define the main execution block.
if __name__ == "__main__":
    # STEP 4: (CRITICAL) We wrap the execution of our Typer CLI
    # within the Flask application's context.
    # This is the "magic" that solves the 'Working outside of application context' error.
    # It ensures that when a command like `ask` calls `forge_new_code`,
    # `forge_new_code` can access `current_app.config`, `current_app.logger`, etc.
    with flask_app.app_context():
        typer_app()
# --- نهاية البروتوكوك- ---
