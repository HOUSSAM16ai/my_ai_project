#!/usr/bin/env python3
import click

from app.cli_handlers.db_cli import register_db_commands
from app.cli_handlers.maintenance_cli import register_maintenance_commands
from app.cli_handlers.migrate_cli import register_migrate_commands
from app.core.di import get_logger, get_session, get_settings


@click.group()
@click.option("--env", default=None, help="Optional env file or label")
@click.pass_context
def cli(ctx, env):
    """A CLI tool for CogniForge."""
    # Initialize settings
    settings = get_settings(env)

    # Initialize logger - get_logger() in app/core/di.py does NOT accept arguments
    logger = get_logger()

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
