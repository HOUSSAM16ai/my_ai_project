# app/cli.py
"""CLI - Command-line interface for application management."""
import os

import click

from app.cli_handlers.db_cli import register_db_commands
from app.cli_handlers.maintenance_cli import register_maintenance_commands
from app.cli_handlers.migrate_cli import register_migrate_commands
from app.core.di import get_logger, get_session, get_settings

@click.group()
@click.option("--env", default=None, help="Optional env file or label")
@click.pass_context
def cli(ctx, env) -> None:
    """A CLI tool for CogniForge."""
    # Handle env file override if provided
    if env:
        os.environ["ENV_FILE"] = env
        # Note: Since settings might be cached or already loaded in di,
        # this might not be perfect without reloading,
        # but standardizing on get_settings() no-arg is the immediate fix for the crash.

    # Initialize settings
    # Fixed: get_settings() takes no arguments in the current DI implementation
    settings = get_settings()

    # Initialize logger
    # Fixed: get_logger() requires a name argument
    logger = get_logger("cli")

    ctx.obj = {
        "settings": settings,
        "logger": logger,
        "get_session": get_session,
    }

register_db_commands(cli)
register_migrate_commands(cli)
register_maintenance_commands(cli)

if __name__ == "__main__":
    cli()
